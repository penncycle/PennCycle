from django import forms

from crispy_forms.layout import Layout, Submit, Div, Field
from crispy_forms.helper import FormHelper
from crispy_forms.bootstrap import InlineRadios

from .models import Student


class SignupForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(SignupForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div(
                    Field(
                        'penncard',
                        placeholder="8 digits",
                    ),
                    'name',
                    'phone',
                    'email', css_class="span5 offset1"
                ), Div(
                    Field(
                        'last_two',
                        placeholder="Usually 00"
                    ),
                    'grad_year',
                    'living_location',
                    InlineRadios('gender'), css_class="span6"
                ), css_class="row-fluid"
            )
        )
        self.helper.form_action = '/signup/'
        self.helper.add_input(Submit('submit', "Submit"))
        self.helper.form_method = 'post'
        self.fields['last_two'].label = "Last two digits of PennCard"
        self.fields['penncard'].label = "PennCard Number"

    class Meta:
        model = Student
        fields = [
            'penncard',
            'name',
            'phone',
            'email',
            'last_two',
            'grad_year',
            'living_location',
            'gender',
        ]

    gender = forms.TypedChoiceField(
        choices=(("M", "Male"), ("F", "Female")),
    )
    
class GroupRideForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(UpdateForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div(
                    'name',
                    'organization',
                    'position_in_organization',
                    'destination', css_class="span5 offset1"
                ), Div(
                    'approximate_duration',
                    'number_bikes',
                    'ispenncycle_representative_needed',
                ), css_class="row-fluid"
            )
        )
        self.helper.form_action = '/groupride/'
        self.helper.add_input(Submit('groupride', "Group Ride Request"))
        self.helper.form_method = 'post'
        self.fields['last_two'].label = "Last two digits of PennCard"

        pass

    '''Name, Organization, Position in Organization,
    Destination of Ride, Approximate duration of the ride, 
    total number of bikes needed (maximum 10). 
    PennCycle representative Lead
    '''

class UpdateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(UpdateForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Div(
                Div(
                    'name',
                    'phone',
                    'pin',
                    'email', css_class="span5 offset1"
                ), Div(
                    'last_two',
                    'grad_year',
                    'living_location',
                ), css_class="row-fluid"
            )
        )
        self.helper.form_action = '/update/'
        self.helper.add_input(Submit('update', "Update"))
        self.helper.form_method = 'post'
        self.fields['last_two'].label = "Last two digits of PennCard"

    class Meta:
        model = Student
        fields = [
            'name',
            'phone',
            'email',
            'last_two',
            'grad_year',
            'living_location',
            'pin'
        ]
