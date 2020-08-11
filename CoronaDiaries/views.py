import pyrebase
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib import auth
import calendar
import time
import random
from datetime import datetime
from pytz import timezone
from tzlocal import get_localzone
from django.views.generic import View 
from django.template.loader import get_template
from .utils import render_to_pdf
from nltk.corpus import wordnet as wn
from itertools import product
from nltk.corpus import stopwords 
from nltk.tokenize import RegexpTokenizer

config = {
    "apiKey": "API-KEY",
    "authDomain": "DOMAIN",
    "databaseURL": "URL",
    "projectId": "PROJECT-ID",
    "storageBucket": "BUCKET",
    "messagingSenderId": "SENDER-ID",
    "appId": "APP-ID",
    "measurementId": "MEASUREMENT-ID"
  }

firebase = pyrebase.initialize_app(config)
fireAuth = firebase.auth()
db = firebase.database()

def signIn(request):
  return render(request, 'login.html')

def home(request):
  if not request.session.has_key("uid"):
    try:
      email = request.POST.get("email")
      password = request.POST.get("password")
      user = fireAuth.sign_in_with_email_and_password(email, password)
      sessionId = user['localId']
      request.session['uid'] = str(sessionId)
    except:
      message = "Invalid credentials"
      return render(request, 'login.html', {"message": message})
  
  localId = request.session['uid']
  name = db.child("Users").child(localId).child("name").get().val()
  return render(request, 'index.html', {"name": name})

def signOut(request):
  try:
    del request.session['uid']
    auth.logout(request)
  except:
    pass
  return render(request, 'login.html')  
  
def signup(request):
  return render(request, 'signup.html')

def signupPost(request):
  name = request.POST.get("name")
  email = request.POST.get("email")
  password = request.POST.get("password")
  try:
    user = fireAuth.create_user_with_email_and_password(email, password)
    uid = user['localId']
    data = {"name": name, "uid": uid}
    db.child("Users").child(uid).set(data)
    return render(request, 'login.html')
  except :
    message = "Unable to create account"
    return render(request, 'signup.html', {"message": message})

def researchPapers(request):
  uid = request.session['uid']
  name = db.child("Users").child(uid).child("name").get().val()
  return render(request, 'researchPapers.html', {"name": name})

def newPaper(request):
  try:
    uid = request.session['uid']
    name = db.child("Users").child(uid).child("name").get().val()
    return render(request, 'newPaper.html', {"name": name})
  except:
    message = "Please sign in to your account first"
    return render(request, 'login.html', {"message": message})

def submitPaper(request):
  uid = request.session['uid']
  name = db.child("Users").child(uid).child("name").get().val()
  title = request.POST.get("title")
  content = request.POST.get("content")
  if title == None or title == "":
    message = "Please enter a title for your paper"
    return render(request, 'newPaper.html', {"message": message})
  elif content == None or content == "":
    message = "Please write some content for your paper"
    return render(request, 'newPaper.html', {"message": message})
  else:
    topics = ["vaccine", "immunity", "prevention", "symptoms", "prediction"]
    selected_topic = ""
    for i in topics:
      if i in title.lower():
        selected_topic = i
        break
    if selected_topic == "":
      filtered_title = removeStopWords(title)
      topicScores = [0 for i in range(5)]
      for i in topics:
        for j in filtered_title:
          scr = closeScore(i, j)
          topicScores[topics.index(i)] = topicScores[topics.index(i)] + scr
      max_score_topic = max(topicScores)
      ind = topicScores.index(max_score_topic)
      selected_topic = topics[ind]
    key = uniqueIdGeneration()
    currTime = getCurrentTime()
    data = {"title": title, "content": content, "author": name, "uid": key, "time": currTime, "topic": selected_topic, "authorID": uid}
    db.child("Papers").child(key).set(data)
    dataForUser = {"title": title, "content": content, "uid": key, "time": currTime, "topic": selected_topic, "authorID": uid, "author": name}
    db.child("Users").child(uid).child("Papers").child(key).set(dataForUser)
    dataForTopic = {"title": title, "content": content, "author": name, "uid": key, "time": currTime, "authorID": uid}
    db.child(selected_topic).child(key).set(dataForTopic)
    return render(request, 'index.html', {"name": name, "message": "Your paper has been submitted under category '"+selected_topic+"'"})

def closeScore(wordx, wordy):
  sem1, sem2 = wn.synsets(wordx), wn.synsets(wordy)
  maxscore = 0
  for i,j in list(product(*[sem1,sem2])):
    score = i.wup_similarity(j) 
    if score != None:
      maxscore = score if maxscore < score else maxscore
  return maxscore

def removeStopWords(sentString):
  sentString = sentString.lower()
  stop_words = set(stopwords.words('english'))
  tokenizer = RegexpTokenizer(r'\w+')
  word_tokens = tokenizer.tokenize(sentString)
  filtered_sentence = []
  for w in word_tokens: 
    if w not in stop_words: 
      filtered_sentence.append(w)
  return filtered_sentence

def uniqueIdGeneration():
  uid = "CORONA-"
  ts = str(calendar.timegm(time.gmtime()))
  uid += ts[:6]
  uid += "-"
  for i in range(8):
    uid += chr(random.randint(65, 90))
  uid += "-"
  uid += ts[6:]
  return uid

def getCurrentTime():
  format = "%Y-%m-%d %H:%M:%S %Z%z"
  now_utc = datetime.now(timezone('UTC'))
  now_local = now_utc.astimezone(get_localzone())
  return now_local.strftime(format)

def myPapers(request):
  uid = request.session['uid']
  name = db.child("Users").child(uid).child("name").get().val()
  mypapers = db.child("Users").child(uid).child("Papers").get().val()
  return render(request, 'myPapers.html', {"name": name, "papers": mypapers})

def viewPaper(request, id):
  uid = request.session['uid']
  name = db.child("Users").child(uid).child("name").get().val()
  curr_paper = db.child("Papers").child(id).get().val()
  return render(request, 'paperView.html', {"curr_paper": curr_paper, "name": name})

class GeneratePDF(View):
  def get(self, request, id, *args, **kwargs):
    template = get_template('download.html')
    curr_paper = db.child("Papers").child(id).get().val()
    context = {"curr_paper": curr_paper}
    html = template.render(context)
    pdf = render_to_pdf('download.html', context)
    return HttpResponse(pdf, content_type='application/pdf')

def topicPapers(request, id):
  uid = request.session['uid']
  name = db.child("Users").child(uid).child("name").get().val()
  papers = db.child(id).get().val()
  topic = id
  return render(request, 'topicPapers.html', {"name": name, "papers": papers, "topic": topic})

def authorPage(request, id):
  uid = request.session['uid']
  name = db.child("Users").child(uid).child("name").get().val()
  papers = db.child("Users").child(id).child("Papers").get().val()
  authorName = db.child("Users").child(id).child("name").get().val()
  return render(request, 'authorPage.html', {"name": name, "papers": papers, "authorName": authorName})

def search(request):
  uid = request.session['uid']
  name = db.child("Users").child(uid).child("name").get().val()
  query = request.POST.get("query").lower()
  query = removeStopWords(query)
  papers = db.child("Papers").get().val()
  search_results = []
  for i in range(len(papers.values())):
    for j in query:
      if j in list(papers.values())[i]['title'].lower() or j in list(papers.values())[i]['topic'].lower():
        result_id = list(papers.values())[i]['uid']
        result = db.child("Papers").child(result_id).get().val()
        search_results.append(result)
        break
  return render(request, 'search.html', {"papers": search_results, "name": name})
