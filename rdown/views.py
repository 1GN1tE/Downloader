from django.shortcuts import render
from django.http import HttpResponse
from .forms import DownloadForm
from urllib import request
import os
import requests
import re
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip
from wsgiref.util import FileWrapper

# Create your views here.
def error_handler(request, text):
    context = {
        'error': text,
    }
    return render(request, 'error.html', context)

def reddit_dn(request):
    global context
    form = DownloadForm(request.POST or None)

    if form.is_valid():
        url = form.cleaned_data.get("url")
        regex = r'^http(?:s)?://(?:www\.)?(?:[\w-]+?\.)?reddit\.com/r/([\w:]{2,21})\/comments\/(\w{5,6})\/(?!comment)(.+?\/)'
        m = re.search(regex, url)
        if m:
            url = format(m.group())[:-1]+".json"
        else:
            return error_handler(request, "Incorrect URL / Not a reddit media URL")

        # print(url)
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
        response = requests.get(url, headers = headers)
        data = response.json()[0]["data"]["children"][0]["data"]

        media_url = data["url"]
        print(media_url, end ="\t\t\t\t")
    
        if 'v.redd.it' in media_url:  # if the post is a video
                print("Detected Post Type: Video")
                video_dn(media_url)
                
        elif 'i.redd.it' in media_url:  # if the post is an image
            if not media_url.endswith('.gif') and not media_url.endswith('.GIF') and not media_url.endswith('.gifv') and not media_url.endswith('.GIFV'):
                return error_handler(request, "Post Type: Image")
            else:
                return error_handler(request, "Post Type: Gif")

        elif "imgur.com" in media_url:
            return error_handler(request, "Imgur not supported")
        else:
            return error_handler(request, "Not a Video")

        context = {
            'form': form,
            'title': data["title"],
            'thumb': data["thumbnail"],
            'author': data["author"],
            'subreddit': data["subreddit_name_prefixed"],
        }

        return render(request, 'red.html', context)

    return render(request, 'red.html', {'form': form})

def video_dn_new(url):
    path = os.path.dirname(os.path.realpath(__file__))+"\\tmp\\"
    if not os.path.exists(path):
        os.mkdir(path)

    # Getting Audio
    hasAudio = False
    try:
        doc = requests.get(url + '/DASH_audio.mp4')
        with open(path + 'Audio.mp3', 'wb') as f:
            f.write(doc.content)
            f.close()
        hasAudio = True
        print("Audio File Downloaded Successfully")
            
    except BaseException as e:
        print(e)
        print(f'Audio file not avaliable')

    # Getting Video
    qualityTypes = [144, 240, 360, 480, 720, 1080]
    for quality in qualityTypes:
        wasDownloadSuccessful = False
        print(f'Trying resolution: {quality}p')
        try:
            request.urlretrieve(
                url + f'/DASH_{quality}.mp4',
                path + f"Video_{quality}.mp4")
            wasDownloadSuccessful = True
            print("Video File Downloaded Successfully")
            
        except BaseException as e:
            print(e)
            print(f'Video file not avaliable at {quality}p going to next resolution')
            continue

        # Merging Audio and Video
        if wasDownloadSuccessful and hasAudio:
            print("Merging Files")
            try:
                clip = VideoFileClip(path + f"Video_{quality}.mp4")
                audioclip = AudioFileClip(path + "Audio.mp3")
                new_audioclip = CompositeAudioClip([audioclip])
                clip.audio = new_audioclip
                try:
                    clip.write_videofile(path + f"Video_Audio_{quality}.mp4", verbose=False, logger=None)
                except Exception as e:
                    pass
                clip.close()
            except Exception as e:
                print("Merge Failed!")
                print(e)
            print("File Successfully Merged")

def video_dn(url):
    path = os.path.dirname(os.path.realpath(__file__))+"\\tmp\\"
    if not os.path.exists(path):
        os.mkdir(path)
        
    # Getting Audio
    hasAudio = False
    try:
        doc = requests.get(url + '/DASH_audio.mp4')
        with open(path + 'Audio.mp3', 'wb') as f:
            f.write(doc.content)
            f.close()
        hasAudio = True
        print("Audio File Downloaded Successfully")
            
    except BaseException as e:
        return error_handler(request, "Audio file not avaliable")

    # Getting Video
    qualityTypes = [1080, 720, 480, 360, 240, 144]
    wasDownloadSuccessful = False
    for quality in qualityTypes:
        print(f'Trying resolution: {quality}p')
        try:
            if path is not None:
                request.urlretrieve(
                    url + f'/DASH_{quality}.mp4',
                    path + "Video.mp4")
                wasDownloadSuccessful = True
                print("Video File Downloaded Successfully")
            else:
                request.urlretrieve(
                    url + f'/DASH_{quality}.mp4', "Video.mp4")
                wasDownloadSuccessful = True
                print("Video File Downloaded Successfully")
            break
        except BaseException as e:
            print(e)
            print(f'Video file not avaliable at {quality}p going to next resolution')
            continue
    if not wasDownloadSuccessful:
        return error_handler(request, "Can't fetch the video file")

    # Merging Audio and Video
    if wasDownloadSuccessful and hasAudio:
        print("Merging Files")
        try:
            clip = VideoFileClip(path + "Video.mp4")
            audioclip = AudioFileClip(path + "Audio.mp3")
            new_audioclip = CompositeAudioClip([audioclip])
            clip.audio = new_audioclip
            try:
                clip.write_videofile(path + "Video_Audio.mp4", verbose=False, logger=None)
            except Exception as e:
                pass
            clip.close()
        except Exception as e:
            return error_handler(request, "Merging Video and Audio Failed")
        
        print("File Successfully Merged")
        os.remove(path + "Video.mp4")
        os.remove(path + "Audio.mp3")

    return path + "Video_Audio.mp4"

def download(request):
    path = "C:\\Users\\arije\\Downloads\\Project\\Downloader\\rdown\\tmp\\Video_Audio.mp4"
    file = FileWrapper(open(path, 'rb'))
    response = HttpResponse(file, content_type='video/mp4')
    response['Content-Disposition'] = 'attachment; filename=' + 'video.mp4'
    return response