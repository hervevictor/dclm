from django import forms
from django.db.models import fields
from .models import Annonce, Message

 

class AnnoncesForm(forms.ModelForm):
    class Meta:
        
        model = Annonce
        fields = ('titre', 'contenu', 'image', 'auteur')  
        
        widgets = {
            'titre' : forms.TextInput(attrs={'class':'form-control'}),
            'contenu' : forms.Textarea(attrs={'class':'form-control'}),
            'image' : forms.FileInput(attrs={'class':'form-control'}),
            'auteur' : forms.TextInput(attrs={'class':'form-control', 'id':'user_id', 'value':'', 'type':'hidden'}),
        }
        

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ('titre', 'message', 'hymnes', 'date', 'auteur')
        
        
        widgets = {
            'titre' : forms.TextInput(attrs={'class':'form-control'}),
            'message' : forms.FileInput(attrs={'class':'form-control'}),
            'hymnes' : forms.Textarea(attrs={'class':'form-control'}),
            'date' : forms.DateInput(attrs={'class':'form-control', 'type':'date'}),
            'auteur' : forms.TextInput(attrs={'class':'form-control', 'id':'user_id', 'value':'', 'type':'hidden'}),
        }




      
        
        