from django.db import models



class Sexe(models.Model):
    name = models.CharField(max_length=100) 
    
    def __str__(self):
        return self.name
    

class Ocupation(models.Model):
    name = models.CharField(max_length=200) 
    def __str__(self):
        return self.name


class Roles(models.Model):
    name = models.CharField(max_length=200) 
    def __str__(self):
        return self.name


class Reponses(models.Model):
    name = models.CharField(max_length=50)
    
    def __str__(self):
        return self.name 



    


