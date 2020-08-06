from time import sleep
from selenium import webdriver
from bs4 import BeautifulSoup
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import play_scraper
import statistics

# This sets up our data fram for storing the data we get from the first part,
# setting our display and creating our first 4 columns
pd.set_option('display.max_columns', 30)
df = pd.DataFrame({
                "rank":[],
                "title":[],
                "developer":[],
                "app_link":[]})

# The webdriver allows us to circumvent cloudflare
driver = webdriver.Chrome(executable_path="/Users/Marko/emp_IO/chromedriver")
driver.implicitly_wait(10)

# This loop iterates the scrapping process for the 5 pages of interest. Because
# each page can display at max 100 apps, we need to iterate 5 times to get the 
# top 500
for i in [1, 2, 3, 4, 5]:
    base_url = "https://www.appbrain.com/stats/google-play-rankings/top_paid/all/us/{}".format(i)
    driver.get(base_url)
    rankings = driver.find_element_by_id('rankings-table')
    htmlString = rankings.get_attribute('innerHTML')
    soup = BeautifulSoup(htmlString, 'html.parser')
    rows = soup.tbody.find_all('tr')
    for row in rows:
        try:
            rank = row.find_all('td', class_='ranking-rank')[0]
            app = row.find_all('td', class_='ranking-app-cell')[0]
            df = df.append({'rank': rank.getText(), 'title': app.a.getText(), 'developer': app.div.a.getText(), 'app_link': app.a['href'].split('/')[-1]}, ignore_index=True )
        except:
            pass
        
# We view the dataframe here to ensure the proper data was collected
print(df)

# Here we create empty lists for our other columns for the datascrape by 
# playscraper package
price = []
genre = []
score = []
reviews_number = []
in_app_purchase = []
range_downloads = []


# This for loop feeds the links for each app from our data frame in the first 
# part to the playscraper module, which then appends the relevant data points
# to our empty lists
for index, row in df.iterrows():
    row_link = row['app_link']
    app_details = play_scraper.details(row_link)
    x= str(app_details['price']).strip('$')
    price.append(float(x)), 
    genre.append(app_details['category']), 
    score.append(app_details['score']), 
    reviews_number.append(app_details['reviews']),
    in_app_purchase.append(app_details['iap']),
    range_downloads.append(app_details['installs']),
		
# This converts our lists to columns in our previous data frame
df['price ($)'] = price
df['genre'] = genre
df['score'] = score
df['reviews_number'] = reviews_number
df['in_app_purchase'] = in_app_purchase

# We check our dataframe and add one more empty list to calculate downloads
print(df)
quant_downloads = []

# Becuase downloads are given as an approximate range, we use the rough rule 
# that downloads can be given approximately as 20 times the number of reviews.
# We limit this by using the range given to us from play scraper as bounds
for downloads, reviews in zip(range_downloads,reviews_number):
    approx = int(reviews)*20
    lowerbound = int(downloads[:-1].replace(',',''))
    
    if approx < lowerbound:
        quant_downloads.append(lowerbound)
    else:
        quant_downloads.append(approx)

print(quant_downloads)

# We assign our approximation of downloads to a column in our dataframe
df['number_downloads'] = quant_downloads
print()
print(df)
print(genre)
print(len(genre))



# We now go about assigning a new genre to entries to limit to 10 groups 
genre_list=[]

# Create a dictionary to map each sub-category (from the page) to our 
# defined categories
genre_dict ={'GAME': ['GAME'],
'FAMILY':['FAMILY','PARENTING'],
'EDUCATION':['EDUCATION','BOOKS_AND_REFERENCE'],
'ENTERTAINMENT':['NEWS_AND_MAGAZINES','ENTERTAINMENT'],
'LIFESTYLE':['HEALTH_AND_FITNESS','SPORTS','LIFESTYLE'],
'MULTIMEDIA':['VIDEO_PLAYER','PHOTOGRAPHY','MUSIC'],
'PRODUCTIVITY':['PERSONALIZATION','COMMUNICATION','BUSINESS','PRODUCTIVITY'],
'UTILITY':['MAPS_AND_NAVIGATION','TOOLS','WEATHER'],
'OUTSIDE_GOOD':['SHOPPING','AUTO_AND_VEHICLES','FOOD_AND_DRINK','MEDICAL','TRAVEL_AND_LOCAL','SOCIAL','FINANCE']
}
         
# We assign the category to each app  
for genre_string in genre:
    g=str(genre_string) 
    
    for catg in genre_dict:
        for i in genre_dict[catg]:
            control=0
            if i in g:
                genre_list.append(catg)
                control=1
                break
# Avoid double entries in case more than one catego in dictionary is present
        if control==1: 
            break
    if control==0:
# Returns a new category which was not added by us in the dictionary,
# if existent
        genre_list.append('OUTSIDE_GOOD') 
                 

df['groups'] = genre_list

# Write to a csv, and quit the browser opened by selenium
df.to_csv('data_Final.csv')
driver.quit()

# We print out a series of summary statistics + the median for each column
stats_file = pd.read_csv('data_Final.csv', delimiter = ',')
print(stats_file)
print(stats_file.describe(include = 'all'))
print(type(stats_file))
print(stats_file.median())

# We set the parameters for our plots of the price against the downloads
x = stats_file['price ($)']
print(x)
y = stats_file['number_downloads']
area = np.pi*3
colors = (0,1,2)

# We define a method to display the scatterplot for only one category
def scatterplot (category,price1,quant_downloads1,gnr_list1,df1):
    array_price = np.array(price1)
    array_downloads = np.array(quant_downloads1)
    array_genre = np.array(gnr_list1)
    array_price = np.array(price1)
    array_downloads = np.array(quant_downloads1)
    array_genre = np.array(gnr_list1)
    df1=pd.DataFrame(dict(x=array_price, y=array_downloads, label=array_genre))
    groups = df1.groupby('label')
    fig, ax = plt.subplots()
    ax.margins(0.05) 
    for name, group in groups:
        if name==category:
            ax.plot(group.x, group.y, marker='o', linestyle='', ms=4, label=name)
    ax.legend()
    
    plt.title(" Top 500 Google play US paid apps")
    plt.xlabel("Price ($USD)")
    plt.ylabel("Number of downloads")
    plt.xlim(0,30)
    plt.ylim(0,0.3*1e7)
    plt.show()
 
# Running the method to display the scatterploty for each category individually
for i in set(genre_list):
    scatterplot(i,price,quant_downloads,genre_list,df)

# Scatterplot of all apps grouped by category (no limitations)
array_price = np.array(price)
array_downloads = np.array(quant_downloads)
array_genre = np.array(genre_list)
df=pd.DataFrame(dict(x=array_price, y=array_downloads, label=array_genre))
groups = df.groupby('label')
fig, ax = plt.subplots()
ax.margins(0.05) 
for name, group in groups:
    ax.plot(group.x, group.y, marker='o', linestyle='', ms=4, label=name)
ax.legend()

# We limit the axes of our scatter plot colored by group to exclude outliers
plt.title(" Top 500 Google play US paid apps")
plt.xlabel("Price ($USD)")
plt.ylabel("Number of downloads")
plt.xlim(0,30)
plt.ylim(0,0.3*1e7)
plt.show()





