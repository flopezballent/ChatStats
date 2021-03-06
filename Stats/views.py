from django.shortcuts import render, redirect, HttpResponse
from.models import Chat
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
from .forms import ChatForm

# Create your views here.

targets = ['eliminó', 
            'añadió', 
            'admin.', 
            'cambió', 
            'Eliminaste', 
            'Añadiste', 
            'Cambiaste', 
            'Saliste', 
            'extremo', 
            'creó', 
            'salió', 
            'Creaste', 
            'videollamada', 
            'llamada']

def checkOs(file):
    for line in file:
        if line[0] == '[':
            return 'iphone'
        else:
            return 'android'

def cleanTxt(file, os):
    if (os == 'android'):
        df = pd.read_csv(file, sep='/n', index_col = False, encoding='utf-8', encoding_errors='ignore', engine='python')
        df = df.iloc[:, 0].str.split(':', expand=True)
        df_msg = df.iloc[:, 2]
        df = df.iloc[:, [0, 1]]
        df_date_hour = df[0].str.split(' ', expand=True).iloc[:,[0,1]]
        name = list(df[1].str.split('-', expand=True).iloc[:,1])
        date = list(df_date_hour[0])
        hour = list(df_date_hour[1])
        message = list(df_msg)
        df = pd.DataFrame({
            'date': date,
            'Day_Hour': hour,
            'name': name,
            'message': message
        })
        df = df.dropna()
        for name in df.name:
            for target in targets:                                    
                if target in name:
                    df = df.drop(df[df.name == name].index)
        return df

    if (os == 'iphone'):
        df = pd.read_csv(file, sep='/n', index_col = False, encoding_errors='ignore', engine='python')
        df = df.iloc[:, 0].str.split(':', expand=True)
        df_msg = df.iloc[:, 3]
        df_name = df.iloc[:, 2].str.split(']', expand=True).iloc[:,1]
        df_date_hour = df.iloc[:, 0]
        df_date_hour = df_date_hour.str.split(' ', expand=True).iloc[:,[0,1]]
        df_date = df_date_hour[0].str.split('[', expand=True).iloc[:,1]
        df_hour = df_date_hour[1]
        message = list(df_msg)
        df = pd.DataFrame({
            'date': list(df_date),
            'Day_Hour': list(df_hour),
            'name': list(df_name),
            'message': message
        })
        df = df.dropna()
        for name in df.name:
            for target in targets:                                    
                if target in name:
                    df = df.drop(df[df.name == name].index)
        return df 

def graphs(df):
    for hour in df.Day_Hour:
        try:
            int(hour)
        except:
            df = df.drop(df[df.Day_Hour == hour].index)
    df['date'] = pd.to_datetime(df['date'], dayfirst=True) 
    df['Day_Hour'] = df['Day_Hour'].astype(int)  
    df['day_week'] = df['date'].dt.day_name() 
    df['month'] = df['date'].dt.month_name()
        
    #Output --> Number of msgs
    total_msj = len(df.index)

    #Output --> Ranking of msgs
    order = df['name'].value_counts().sort_values(ascending=False).to_dict()
    ranking = sorted(order.items(), key=lambda x: x[1], reverse=True)
    first = ranking[0]
    rank = ranking[1:]

    #Output --> Ranking per year
    fig = plt.figure(figsize=(8,5))
    ax = sns.countplot(y='name', data=df, order = df['name'].value_counts().index, hue=df['date'].dt.year, palette="crest")
    ax.set(ylabel=None)
    plt.savefig('media/graphs/rank-per-year.png', transparent=True, bbox_inches='tight')

    #Output --> Chronology
    per = df.date.dt.to_period("M")
    df_crono = df.groupby(per).size().reset_index(name='counts')
    df_crono['date'] = df_crono['date'].astype(str)
    fig = plt.figure(figsize=(12, 5))
    ax = sns.lineplot(x='date', y='counts', data=df_crono)
    ax.set(ylabel=None)
    plt.xticks(rotation=90)
    plt.grid()
    plt.savefig('media/graphs/chronology.png', transparent=True, bbox_inches='tight')

    #Output --> Histogram
    fig = plt.figure(figsize=(8, 4))
    ax = sns.histplot(df, x=df['Day_Hour'], palette="crest", bins=24)
    ax.set(ylabel=None, xticks=[*range(0,24)], xticklabels=[*range(0,24)])
    plt.savefig('media/graphs/histogram.png', transparent=True)

    #Output --> Messages per Week
    fig = plt.figure(figsize=(8, 4))
    ax = sns.countplot(y='day_week', data=df, order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'], palette="crest")
    ax.set(ylabel=None)
    plt.savefig('media/graphs/week.png', transparent=True, bbox_inches='tight')

    #Output --> Messages per Year
    fig = plt.figure(figsize=(8, 4))
    ax = sns.countplot(y='month', data=df, order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'], palette="crest")
    ax.set(ylabel=None)
    plt.savefig('media/graphs/year.png', transparent=True, bbox_inches='tight')

    return first, rank, total_msj

def keygraph(df, key):
    df['key_detector'] = df['message'].str.contains(key, regex=True)
    df_key = df.groupby(['name', 'key_detector']).size().reset_index(name='counts')
    df_key_true = df_key.loc[df_key['key_detector']]
    fig = plt.figure(figsize=(8,4))
    ax = sns.barplot(y='name', x='counts', data=df_key_true, palette="crest")
    ax.set(title = f'Word: "{key}"', ylabel=None)
    plt.savefig('media/graphs/key.png', transparent=True, bbox_inches='tight')

def home(request):
    global df
    if request.method=='POST':
        form = ChatForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            path = Chat.objects.last().file.path
            with open(path, 'r',encoding='utf-8') as f:
                file = f.name
                txt = f
                try:
                    os_chat = checkOs(txt)
                except:
                    return HttpResponse('I can only read .txt files :(')
            df = cleanTxt(file, os_chat)
            os.remove(path)
            Chat.objects.filter(file = Chat.objects.last().file).delete()
            return redirect('/results')
    else:
        form = ChatForm()
        context = {
            'form': form,
        }

    return render(request, 'Stats/index.html', context)

def results(request):
    global df
    if request.method == 'POST':
        key = request.POST.get('key')
        keygraph(df, key)
        return redirect("/results/?key")

    results = graphs(df)
    first, rank , total_msj = results[0], results[1], results[2] 

    context = {
        'total_msj': total_msj,
        'rank': rank,
        'first': first,
    }

    return render(request, 'Stats/results.html', context)
