from bs4 import BeautifulSoup
import json
import csv
from flask import Flask, render_template, request, jsonify, redirect
import re
import requests
import os

app = Flask(__name__)


@app.route('/how')
def how():
    return render_template('how.html')

# Function to scrape Google search results
def scrape_google_results(query, num_results, convert_links):
    results = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
    }

    for start in range(0, num_results, 10):
        url = f"https://www.google.com/search?q={query}&start={start}"
        print(url)
        response = requests.get(url, headers=headers)
        print(response)
        soup = BeautifulSoup(response.text, 'html.parser')
        search_results = soup.find_all('a')

        for result in search_results:
            link = result.get('href')
            if link:
                print(link, '/channel' in link or '/@' in link or '/c' in link)
                if '/channel' in link or '/@' in link or '/c' in link:
                    results.append('https://' + str(link))
                if '/watch?v' in link:
                    if convert_links:
                        channel_url = get_channel_url(link)
                        if channel_url:
                            results.append(channel_url)
                    else:
                        results.append('https://' + str(link))

    return results[:num_results]

# Function to save results as JSON
def save_as_json(results, file_name):
    with open(file_name, 'w') as f:
        json.dump(results, f, indent=4)

# Function to save results as CSV
def save_as_csv(results, file_name):
    with open(file_name, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['YouTube Channel Link'])
        writer.writerows([[link] for link in results])

# Route for the home page
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        site_name = "youtube.com"
        query = request.form.get('query')
        num_results = int(request.form.get('num_results'))
        convert_links = request.form.get('convert_links')
        if convert_links == "on":
            convert_links = True
        else:
            convert_links = False

        if not query or not num_results:
            return render_template('index.html', message='Please provide query and number of results.')

        formatted_query = f'site:{site_name}+{query}'

        # Scrape Google search results
        results = scrape_google_results(formatted_query, num_results, convert_links)

        # Save results in JSON format
        save_as_json(results, 'static/youtube_links.json')

        # Save results in CSV format
        save_as_csv(results, 'static/youtube_links.csv')

        return redirect('/download')

    return render_template('index.html')


@app.route('/download')
def download():
    return render_template('downloadPage.html', message='Scraping completed.')





def get_channel_url(video_url):
    # Extract the channel ID from the video URL
    channel_id = None
    if 'youtube.com/watch' in video_url:
        params = video_url.split('?')[1]
        for param in params.split('&'):
            if param.startswith('v='):
                video_id = param.split('=')[1]
                break
        if video_id:
            api_url = f"https://www.googleapis.com/youtube/v3/videos?id={video_id}&key=AIzaSyAOrHxGgzR_U19AAUcn4IWyBAGgafvTKhw&part=snippet"
            response = requests.get(api_url)
            video_data = response.json()
            if 'items' in video_data:
                channel_id = video_data['items'][0]['snippet']['channelId']
    elif 'youtu.be/' in video_url:
        video_id = video_url.split('/')[-1]
        api_url = f"https://www.googleapis.com/youtube/v3/videos?id={video_id}&key=AIzaSyAOrHxGgzR_U19AAUcn4IWyBAGgafvTKhw&part=snippet"
        response = requests.get(api_url)
        video_data = response.json()
        if 'items' in video_data:
            channel_id = video_data['items'][0]['snippet']['channelId']

    # Construct the channel URL
    if channel_id:
        channel_url = f"https://www.youtube.com/channel/{channel_id}"
        return channel_url
    else:
        return "Could not be converted"



    

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=5000)