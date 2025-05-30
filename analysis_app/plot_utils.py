import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.graphics.gofplots import qqplot
from statsmodels.graphics.tsaplots import plot_acf
import io, base64

plt.style.use('seaborn-v0_8-whitegrid')


def _fig_to_base64():
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    img = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()
    return img


def generate_price_plot(df):
    plt.figure(figsize=(12, 6))
    for col in df.columns:
        plt.plot(df.index, df[col], label=col)
    plt.title('Динамика цен закрытия')
    plt.xlabel('Дата')
    plt.ylabel('Цена')
    plt.legend()
    return _fig_to_base64()


def generate_correlation_heatmap(corr):
    plt.figure(figsize=(8, 6))
    sns.heatmap(corr, annot=True, cmap='coolwarm', fmt='.2f', linewidths=.5)
    plt.title('Тепловая карта корреляционной матрицы доходностей')
    return _fig_to_base64()


def generate_regression_plot(y_true, y_pred, name):
    plt.figure(figsize=(10, 6))
    plt.scatter(y_true, y_pred, alpha=.5)
    m, M = min(y_true.min(), y_pred.min()), max(y_true.max(), y_pred.max())
    plt.plot([m, M], [m, M], 'r--', lw=2)
    plt.title(f'Регрессия: фактические vs предсказанные {name}')
    plt.xlabel(f'Фактические {name}')
    plt.ylabel(f'Предсказанные {name}')
    return _fig_to_base64()


def generate_residuals_plot(residuals, name):
    plt.figure(figsize=(10, 6))
    plt.scatter(residuals.index, residuals, alpha=.5)
    plt.axhline(0, color='red', ls='--')
    plt.title(f'Остатки регрессии {name}')
    plt.xlabel('Наблюдение')
    plt.ylabel('Остаток')
    return _fig_to_base64()


def generate_residuals_hist(residuals, name):
    plt.figure(figsize=(8, 5))
    sns.histplot(residuals, kde=True, bins=30)
    plt.title(f'Гистограмма остатков {name}')
    plt.xlabel('Остаток')
    return _fig_to_base64()


def generate_qq_plot(residuals, name):
    plt.figure(figsize=(6, 6))
    qqplot(residuals, line='s', ax=plt.gca())
    plt.title(f'QQ-plot остатков {name}')
    return _fig_to_base64()


def generate_acf_plot(residuals, name):
    plt.figure(figsize=(8, 4))
    plot_acf(residuals, ax=plt.gca(), lags=40, zero=False)
    plt.title(f'ACF остатков {name}')
    return _fig_to_base64()


def generate_pairplot(returns):
    sns.pairplot(returns, kind='scatter', corner=True, diag_kind='kde', plot_kws={'alpha': .5})
    return _fig_to_base64()
