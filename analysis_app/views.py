import io
import os

import numpy as np
import pandas as pd
import statsmodels.api as sm
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse, Http404
from django.shortcuts import render
from django.template.loader import render_to_string
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.stattools import durbin_watson, jarque_bera
from weasyprint import HTML, CSS

from .forms import FileUploadForm
from .plot_utils import (
    generate_price_plot,
    generate_correlation_heatmap,
    generate_regression_plot,
    generate_residuals_plot,
    generate_residuals_hist,
    generate_qq_plot,
    generate_acf_plot,
    generate_pairplot,
)

MIN_FILES_FOR_ANALYSIS = 2


def parse_uploaded_files(files):
    data_frames, tickers = [], []
    for f in files:
        ticker = os.path.splitext(f.name)[0].upper()
        if not ticker:
            return None, None, f"Не удалось определить тикер для файла {f.name}."
        df = pd.read_csv(io.BytesIO(f.read()), skiprows=3, header=None, usecols=[0, 1])
        df.columns = ['Date', 'Close']
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        df.rename(columns={'Close': ticker}, inplace=True)
        df = df[~df.index.duplicated(keep='first')]
        data_frames.append(df)
        tickers.append(ticker)
    if not data_frames:
        return None, None, "Не удалось обработать ни один из файлов."
    combined = pd.concat(data_frames, axis=1).dropna()
    if combined.empty or len(combined) < 2:
        return None, None, "Недостаточно общих данных."
    return combined, tickers, None


def analysis_view(request):
    form = FileUploadForm(request.POST or None, request.FILES or None)
    ctx = {'form': form, 'MIN_FILES_FOR_ANALYSIS': MIN_FILES_FOR_ANALYSIS}
    if request.method == 'POST':
        if not form.is_valid():
            messages.error(request, "Пожалуйста, исправьте ошибки.")
            return render(request, 'upload_page.html', ctx)
        files = form.cleaned_data['csv_files']
        if len(files) < MIN_FILES_FOR_ANALYSIS:
            err = f"Для анализа необходимо ≥{MIN_FILES_FOR_ANALYSIS} файла."
            form.add_error('csv_files', err)
            messages.error(request, err)
            return render(request, 'upload_page.html', ctx)
        dv_input = form.cleaned_data.get('dependent_variable', '').upper()
        combined, tickers, err = parse_uploaded_files(files)
        if err:
            form.add_error('csv_files', err)
            messages.error(request, err)
            return render(request, 'upload_page.html', ctx)
        returns = np.log(combined / combined.shift(1)).dropna()
        if returns.empty or len(returns) < 2:
            messages.error(request, "Недостаточно данных для расчёта доходностей.")
            return render(request, 'upload_page.html', ctx)
        corr = returns.corr()
        dv = dv_input if dv_input in returns.columns else tickers[0]
        iv = [c for c in returns.columns if c != dv]
        reg_summary = 'Не удалось провести регрессию.'
        reg_plot = res_plot = res_hist = qq_plot = acf_plot = None
        dw_stat = jb_stat = jb_p = None
        vif_html = ''
        if iv:
            Y = returns[dv]
            X = sm.add_constant(returns[iv])
            model = sm.OLS(Y, X).fit()
            reg_summary = model.summary().as_text()
            y_pred = model.predict(X)
            reg_plot = generate_regression_plot(Y, y_pred, dv)
            res_plot = generate_residuals_plot(model.resid, dv)
            res_hist = generate_residuals_hist(model.resid, dv)
            qq_plot = generate_qq_plot(model.resid, dv)
            acf_plot = generate_acf_plot(model.resid, dv)
            dw_stat = round(durbin_watson(model.resid), 4)
            jb_stat, jb_p, _, _ = jarque_bera(model.resid)
            vif = pd.DataFrame({'Variable': X.columns[1:],
                                'VIF': [variance_inflation_factor(X.values, i + 1) for i in range(len(iv))]})
            vif_html = vif.to_html(classes='table table-bordered table-sm', index=False)
        pairplot = generate_pairplot(returns)
        result_ctx = {
            'tickers': tickers,
            'start_date': combined.index.min().strftime('%Y-%m-%d'),
            'end_date': combined.index.max().strftime('%Y-%m-%d'),
            'common_days_count': len(combined),
            'combined_data_html': combined.head().to_html(classes='table table-striped table-sm'),
            'returns_data_html': returns.head().to_html(classes='table table-striped table-sm'),
            'correlation_matrix_html': corr.to_html(classes='table table-bordered table-sm'),
            'price_plot_base64': generate_price_plot(combined),
            'correlation_heatmap_base64': generate_correlation_heatmap(corr),
            'pairplot_base64': pairplot,
            'dependent_var_reg': dv,
            'independent_vars_reg': iv,
            'regression_summary_text': reg_summary,
            'regression_plot_base64': reg_plot,
            'residuals_plot_base64': res_plot,
            'residuals_hist_base64': res_hist,
            'qq_plot_base64': qq_plot,
            'acf_plot_base64': acf_plot,
            'dw_stat': dw_stat,
            'jb_stat': jb_stat,
            'jb_pvalue': jb_p,
            'vif_html': vif_html,
        }
        request.session['analysis_results_context'] = result_ctx
        return render(request, 'results_page.html', result_ctx)
    return render(request, 'upload_page.html', ctx)


def download_pdf_view(request):
    if request.method == 'POST':
        ctx = request.session.get('analysis_results_context')
        if not ctx:
            raise Http404
        html_string = render_to_string('results_page.html', ctx)
        css_file = os.path.join(settings.STATICFILES_DIRS[0], 'css', 'custom_style.css')
        stylesheets = [
            CSS(string='@import url("https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css");')]
        if os.path.exists(css_file):
            stylesheets.append(CSS(filename=css_file))
        pdf_bytes = HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf(
            stylesheets=stylesheets)
        resp = HttpResponse(pdf_bytes, content_type='application/pdf')
        resp['Content-Disposition'] = 'attachment; filename="financial_analysis_report.pdf"'
        return resp
    return HttpResponse(status=405)
