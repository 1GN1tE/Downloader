from django.shortcuts import render
from django.http import HttpResponse
import youtube_dl
from .forms import DownloadForm
import re

# Create your views here.
def video_dn(request):
    global context
    form = DownloadForm(request.POST or None)

    if form.is_valid():
        video_url = form.cleaned_data.get("url")
        regex = r'^(http(s)?:\/\/)?((w){3}.)?youtu(be|.be)?(\.com)?\/.+'
        if not re.match(regex,video_url):
            return render(request, 'error.html')
    
        ydl_opts = {}
        try:
            # Get metadata of video
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                meta = ydl.extract_info(video_url, download=False)
            
            # Parse metadata
            video_streams = []
            audio_streams = []
            for m in meta['formats']:
                file_size = m['filesize']

                if file_size is None:
                    continue

                file_size = f'{round(int(file_size) / 1000000,2)} mb'
               
                if 'audio' in m['format']:
                    # Audio Streams
                    audio_streams.append({
                        'extension': m['ext'],
                        'file_size': file_size,
                        'video_url': m['url']
                    })
                else:
                    # Video streams
                    resolution = f"{m['height']}x{m['width']}"
                    video_streams.append({
                        'resolution': resolution,
                        'extension': m['ext'],
                        'file_size': file_size,
                        'video_url': m['url']
                    })

            video_streams = video_streams[::-1]
            audio_streams = audio_streams[::-1]

            # Send parsed data as response
            context = {
                'form': form,
                'title': meta.get('title', None),
                'stream_video': video_streams,
                'stream_audio': audio_streams,
                'description': meta.get('description'),
                'likes': f'{int(meta.get("like_count", 0)):,}',
                # 'dislikes': f'{int(meta.get("dislike_count", 0)):,}',
                'thumb': meta.get('thumbnails')[3]['url'],
                'duration': round(int(meta.get('duration', 1))/60, 2),
                'views': f'{int(meta.get("view_count")):,}'
            }
            return render(request, 'home.html', context)
        except Exception as error:
            return HttpResponse(error.args[0])
    return render(request, 'home.html', {'form': form})
