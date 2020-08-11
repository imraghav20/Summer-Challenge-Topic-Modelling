"""CoronaDiaries URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', views.signIn, name="signIn"),
    path('', views.home, name="home"),
    path('logout/', views.signOut, name="signOut"),
    path('signup/', views.signup, name="signup"),
    path('signuppost/', views.signupPost, name="signupPost"),
    path('researchpapers/', views.researchPapers, name="researchPapers"),
    path('newpaper/', views.newPaper, name="newPaper"),
    path('submitPaper/', views.submitPaper, name="submitPaper"),
    path('myPapers/', views.myPapers, name="myPapers"),
    path('papers/<str:id>', views.viewPaper, name="viewPaper"),
    path('download/<str:id>', views.GeneratePDF.as_view(), name="downloadPaper"),
    path('researchpapers/<str:id>', views.topicPapers, name="topicPapers"),
    path('authors/<str:id>', views.authorPage, name="authorPage"),
    path('searchresults', views.search, name="search")
]
