import re

from django import forms

from .models import EventRegistration

_INPUT = ("w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm text-gray-800 "
          "focus:border-lapomed-gold focus:ring-1 focus:ring-lapomed-gold outline-none")


def valida_cpf(num):
    """Valida CPF pelos dígitos verificadores. Recebe só dígitos."""
    cpf = re.sub(r"\D", "", num or "")
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for i in (9, 10):
        soma = sum(int(cpf[n]) * ((i + 1) - n) for n in range(i))
        dig = (soma * 10) % 11 % 10
        if dig != int(cpf[i]):
            return False
    return True


class EventRegistrationForm(forms.ModelForm):
    # honeypot anti-robô: campo invisível que humanos deixam vazio
    website = forms.CharField(required=False, widget=forms.HiddenInput)
    consent = forms.BooleanField(
        required=True,
        label="Autorizo o uso dos meus dados para a organização deste evento (LGPD).",
    )

    class Meta:
        model = EventRegistration
        fields = ["name", "email", "document_type", "document_number", "institution", "consent"]
        labels = {
            "name": "Nome completo",
            "email": "E-mail",
            "document_type": "Tipo de documento",
            "document_number": "Nº do documento",
            "institution": "Universidade / Instituição",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name in ("consent", "website"):
                continue
            if isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = _INPUT + " bg-white"
            else:
                field.widget.attrs["class"] = _INPUT
        self.fields["document_type"].required = False
        self.fields["document_number"].required = False

    def clean(self):
        cleaned = super().clean()
        dtype = cleaned.get("document_type")
        dnum = cleaned.get("document_number")
        if dtype == "cpf" and dnum and not valida_cpf(dnum):
            self.add_error("document_number", "CPF inválido.")
        if dtype and not dnum:
            self.add_error("document_number", "Informe o número do documento.")
        return cleaned

    def is_bot(self):
        return bool(self.data.get("website"))
