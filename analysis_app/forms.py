# finance_analysis/analysis_app/forms.py
from django import forms

class MultipleFileInput(forms.ClearableFileInput):
    """File input, понимающий множественный выбор."""
    allow_multiple_selected = True   # <— снимает защиту CVE-2023-31047

    def value_from_datadict(self, data, files, name):
        """
        Django стандартно берёт только один файл (files.get),
        нам нужно весь список.
        """
        if hasattr(files, "getlist"):
            return files.getlist(name)
        return []

class MultipleFileField(forms.FileField):
    """
    FileField, который принимает список UploadedFile,
    валидирует каждый по очереди и возвращает список.
    """
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        # required=True → проверка, что список не пуст
        if self.required and not data:
            raise forms.ValidationError("Необходимо выбрать хотя бы один файл.")
        # когда загружен ровно один файл — data может быть UploadedFile
        if not isinstance(data, (list, tuple)):
            data = [data]
        cleaned_files = []
        single_clean = super().clean
        for f in data:
            cleaned_files.append(single_clean(f, initial))
        return cleaned_files

class FileUploadForm(forms.Form):
    csv_files = MultipleFileField(
        label='Загрузите CSV файлы (минимум 2 для анализа)',
        help_text='Удерживайте Ctrl (или Cmd) для выбора нескольких файлов.',
        required=True,
        widget=MultipleFileInput(attrs={'class': 'form-control'}),
    )
    dependent_variable = forms.CharField(
        label='Тикер зависимой переменной (Y) для регрессии',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text='Укажите тикер одной из загруженных бумаг (например, AAPL). '
                  'Можно оставить пустым — возьмётся первый тикер.',
        required=False,
    )
