# -*- coding: utf-8 -*-
"""GrubhubStats.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/18NqG12yk8CUsT7Ignn_XFzF8nQokjRu5
"""

import email, getpass, imaplib, os, re
import base64
import re
import datetime
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import datetime as dt
import matplotlib.dates as mdates
import csv
from collections import Counter

"""
Make sure to allow less secure apps on your gmail settings
"""
class GrubhubStats:
  ymd = None
  hms = None
  ym = None
  subtotals = None
  names = None
  addy = None
  orders = None
  orderCounter = None
  repeatPerc = 0

  def __init__(self,username,password,label):
    self.m = imaplib.IMAP4_SSL("imap.gmail.com")
    self.m.login(username, password)
    self.m.select(label)

  def genDates(self):
    self.ymd = []
    self.hms = []
    self.ym = []
    typ, data = self.m.search(None, 'FROM orders@eat.grubhub.com')
    for num in data[0].split():
      #calculate and store time
      typ, data = self.m.fetch(num, "(UID BODY[TEXT])")
      s ='Message %s\n%s\n' % (num, data[0][1])
      s = re.sub('<[^<]+?>', '',s) 
      s = s.replace("=\\r\\n", "")
      ind = s.find("Order placed on:  ") + 18
      dt = s[ind:ind+25].strip()
      if dt.find(":") != -1:
        #newerOrderFormat
        tt = dt[dt.rfind(",")+1:]
        tt = datetime.datetime.strptime(tt," %I:%M:%S %p")
        self.hms.append(tt)
        dd = dt[:dt.rfind(","):]
        ym = dd[:3] + " " + dd[len(dd)-4:]
        dd = datetime.datetime.strptime(dd,"%b %d, %Y")
        ym = datetime.datetime.strptime(ym,"%b %Y")
        self.ymd.append(dd)
        self.ym.append(ym)

      #oldeOrderFormat
      elif s.find("Deliver by") != -1:
        ind = s.find("Deliver by")
        dt = s[ind+13:ind+36]
        tt = dt[dt.rfind(",")+2:]
        tt = tt.rstrip(" ")
        tt = datetime.datetime.strptime(tt,"%I:%M %p")
        self.hms.append(tt)
        dd = dt[:dt.rfind(",")]
        ym = dd[:3] + " " + dd[len(dd)-4:]
        dd = datetime.datetime.strptime(dd,"%b %d, %Y")
        ym = datetime.datetime.strptime(ym,"%b %Y")
        self.ymd.append(dd)
        self.ym.append(ym)
      elif s.find("Ready for pickup by   ") != -1:
        ind = s.find("Ready for pickup by   ")
        dt = s[ind+22:ind+44]
        tt = dt[dt.rfind(",")+2:]
        tt = tt.rstrip(" ")
        tt = datetime.datetime.strptime(tt,"%I:%M %p")
        self.hms.append(tt)
        dd = dt[:dt.rfind(",")]
        ym = dd[:3] + " " + dd[len(dd)-4:]
        dd = datetime.datetime.strptime(dd,"%b %d, %Y")
        ym = datetime.datetime.strptime(ym,"%b %Y")
        self.ymd.append(dd)
        self.ym.append(ym)
      else:
        #odd formatting
        self.hms.append(None)
        self.ym.append(None)
        self.ymd.append(None)
    
  def orderTotals(self):
    self.subtotals = []
    typ, data = self.m.search(None, 'FROM orders@eat.grubhub.com')
    for num in data[0].split():
      #calculate and store time
      typ, data = self.m.fetch(num, "(UID BODY[TEXT])")
      s ='Message %s\n%s\n' % (num, data[0][1])
      s = re.sub('<[^<]+?>', '',s) 
      s = s.replace("=\\r\\n", "")
      ind = s.find("Subtotal")
      s = s[ind:]
      ind = s.find("$")
      s = s[ind+1:]
      ind = s.find(" ")
      subtotal = float(s[:ind])
      self.subtotals.append(subtotal)

  def getCustomerName(self, repeat = True):
    self.names = []
    self.addy = []
    namedc = {}
    count = 0
    repeat = 0
    typ, data = self.m.search(None, 'FROM orders@eat.grubhub.com')
    for num in data[0].split():
      #calculate and store time
      typ, data = self.m.fetch(num, "(UID BODY[TEXT])")
      s ='Message %s\n%s\n' % (num, data[0][1])
      s = re.sub('<[^<]+?>', '',s) 
      s = s.replace("=\\r\\n", "")
      ind = s.find("Deliver to:")
      if ind != -1:
        s = s[ind+12:]
        ind = s.find(", NY 1")
        s = s[:ind-9]
        s = s.rstrip(" ")
        ind = s.find("   ")
        name = s[:ind]
        addy = s[ind+3:]
        self.names.append(name)
        self.names.append(addy)
        if addy not in namedc:
          namedc[addy] = True
        elif namedc[addy] == True:
          repeat +=1
        else:
          count -=1
        count+=1
      if s.find("DELIVERY") == -1:
        self.names.append("PICKUP")
      else:
        self.addy.append(addy)
    self.repeatPerc = repeat/count
    print(self.repeatPerc)
      #Deliver to: Ana R   121 Reade St     APT 7A     New York, NY 10013

  def getOrder(self,count=True):
    #figure out how to deal w delivery special!!!!
    self.orders = []
    self.orderCounter = Counter()
    typ, data = self.m.search(None, 'FROM orders@eat.grubhub.com')
    nume=0
    for num in data[0].split():
      #calculate and store time
      typ, data = self.m.fetch(num, "(UID BODY[TEXT])")
      s ='Message %s\n%s\n' % (num, data[0][1])
      s = re.sub('<[^<]+?>', '',s) 
      s = s.replace("=\\r\\n", "")
      s = s.replace("\\r\\n", "")
      s = s.replace( "\\t" ," ") 
      s= s.replace("=20","")
      s= s.replace("=09","")
      ind = s.find("Price ") + len("Price")
      s = s[ind:s.find("Include napkins and utensils?")]
      items = []
      s = s.lstrip(" ")
      item = ""
      while s.strip(" ") != "":
        if s[0].isnumeric():
          num = s[0]
          item = s[1:s.find("$")]
          if item.find("Instructions:") != -1:
            item = item[:item.find("Instructions:")]
          item = item.strip()
          for i in range(1):
              if item.find("Price") != -1:
                item = item[item.find("1")+1:]
                item = item.lstrip(" ")
              items.append(item)
          s = s[s.find("$")+7:]
          s = s.lstrip(" ")
          if count == True:
            self.orderCounter[item] +=1
        else:
          s = s.lstrip(" ")
          ind = s.find("                  ") + 18
          s = s[ind:]
        #print(item + "item")
        #print(s + "string")
        if (item == "Meal for One" or item == "Meal for Two" or item == "Meal for Three") or ("Combo" in item):
          cParse = s[:s.find("        ")]
          cParse = cParse.split("  ")
          #print(cParse)
          #print("cParse")
          if "" not in cParse:
            for i in cParse:
              self.orderCounter[i]+=1
      self.orders.append(items)
    print(self.orderCounter)
    

  #need to run all methods
  def generateCSV(self):
    with open('output.csv', 'w', newline='') as f:
      writer = csv.writer(f, delimiter=' ')
      writer.writerows([self.md,self.hms,self.ym,self.subtotals,self.names,self.addy])

  def ordersByTime(self,frequency = '30Min'):
    df = pd.DataFrame({'times':self.times})
    df['Operating Hours']=pd.to_datetime(df['times'],format='%H:%M')
    df.set_index('Operating Hours', drop=False, inplace=True)
    ax = df['Operating Hours'].groupby(pd.Grouper(freq=frequency)).count().plot(kind='bar', color='b',title="Online Ordering By Hour")
    ax.set_xticklabels([t.get_text().rsplit(" ")[1] for t in ax.get_xticklabels()])
    ax.set_ylabel("Number of Orders")