from moviepy.editor import AudioFileClip
import speech_recognition
import subprocess
import json
import os
import re

def get_video_title(link):
    """
    The function `get_video_title` takes a YouTube video link as input and returns the sanitized title
    of the video.
    
    :param link: The `link` parameter is the URL of the YouTube video for which you want to retrieve the
    title
    :return: the sanitized title of the video extracted from the given link.
    """
    process = subprocess.Popen(['yt-dlp', '--get-title', link], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, _ = process.communicate()
    video_title = stdout.decode().strip()
    sanitized_title = re.sub(r'[<>:"/\\|?*]', '_', video_title)
    return sanitized_title

def download_video(link, directory, video_title):
    """
    The `download_video` function downloads a video from a given link and saves it as an MP3 file in the
    specified directory with the provided video title.
    
    :param link: The link parameter is the URL of the video that you want to download. It should be a
    valid YouTube video link
    :param directory: The `directory` parameter is the path to the directory where you want to save the
    downloaded video. It should be a string representing the directory path on your system. For example,
    if you want to save the video in the "Downloads" folder, you can pass the directory parameter as
    `"/Users
    :param video_title: The `video_title` parameter is the title of the video that you want to download.
    It will be used to name the downloaded file
    """
    output_filename = f'{video_title}.%(ext)s'
    command = f'yt-dlp -x --audio-format mp3 -o "{os.path.join(directory, output_filename)}" -f "bestaudio/best" {link}'
    subprocess.run(command, shell=True, check=True)

def download_playlist(playlist_url):
    """
    The function `download_playlist` takes a playlist URL as input, downloads the playlist metadata
    using `yt-dlp`, and returns the playlist title, titles of individual videos in the playlist, and
    their corresponding URLs.
    
    :param playlist_url: The `playlist_url` parameter is the URL of the YouTube playlist that you want
    to download
    :return: The function `download_playlist` returns a tuple containing the playlist title, a list of
    titles of the videos in the playlist, and a list of URLs of the videos in the playlist.
    """
    command = f"yt-dlp -J --flat-playlist {playlist_url}"
    output = subprocess.check_output(command, shell=True)
    data = json.loads(output)
    playlist_title = data['title']
    entries = data['entries']
    titles = [item['title'] for item in entries]
    urls = [item['url'] for item in entries]
    return playlist_title, titles, urls

def convert_audio_to_text(audio_file, video_title=None):
    """
    The function `convert_audio_to_text` takes an audio file as input, converts it to a WAV file, uses
    speech recognition to transcribe the audio to text, and saves the text in a text file.
    
    :param audio_file: The audio file path or name that you want to convert to text. It should be in a
    format that is supported by the audio file clip library
    :param video_title: The `video_title` parameter is an optional parameter that represents the title
    of the video. If provided, it will be used to generate the output file name by appending ".txt" to
    the video title. If not provided, the output file name will be generated based on the name of the
    audio file
    :return: The function does not explicitly return anything.
    """
    audio = AudioFileClip(audio_file)
    temp_wav_path = os.path.splitext(audio_file)[0] + ".wav"
    audio.write_audiofile(temp_wav_path, codec='pcm_s16le')
    recognizer = speech_recognition.Recognizer()
    with speech_recognition.AudioFile(temp_wav_path) as audio_file:
        audio = recognizer.record(audio_file)
    
    try:
        text = recognizer.recognize_google(audio)
    except speech_recognition.RequestError as e:
        print("Recognition connection failed:", e)
        return
    
    if video_title:
        output_file_name = video_title + ".txt"
    else:
        output_file_name = os.path.splitext(audio_file)[0] + ".txt"
    
    with open(output_file_name, "w") as output_file:
        output_file.write(text)
    
    os.remove(temp_wav_path)

def merge_text_files(directory, merged_file_name):
    """
    The function `merge_text_files` merges multiple text files into a single file, with each file's
    content separated by a header.
    
    :param directory: The directory parameter is the path to the directory where the text files are
    located
    :param merged_file_name: The `merged_file_name` parameter is the name of the file that will be
    created after merging all the text files. It should be a string without the file extension. For
    example, if you want the merged file to be named "merged_text.txt", then the `merged_file_name`
    parameter should
    """
    merged_file = os.path.join(directory, merged_file_name + ".txt")
    text_files = [file for file in os.listdir(directory) if file.endswith(".txt") and file != merged_file_name + ".txt" and file != "filenames.txt"]
    
    with open(merged_file, "w") as merged_file_obj:
        for file_name in text_files:
            with open(os.path.join(directory, file_name), "r") as file:
                merged_file_obj.write("// " + file_name + "\n")
                merged_file_obj.write(file.read())
                merged_file_obj.write("\n\n")
    
    for file in text_files:
        os.remove(os.path.join(directory, file))

if __name__ == "__main__":
    single_video_download = int(input("Enter\n1. To convert one video to text\n2. To convert a playlist to text"))    

    if single_video_download == 1:
        link = input("Enter the link you want to download: ")
        video_title = get_video_title(link)
        folder_path = os.path.join(os.getcwd(), video_title)
        os.makedirs(folder_path, exist_ok=True)
        download_video(link, folder_path, video_title)
        convert_audio_to_text(os.path.join(folder_path, f"{video_title}.mp3"), video_title)
    
    elif single_video_download == 2:
        link = input("Enter the playlist link you want to download: ")
        filename, titles, urls = download_playlist(link)
        folder_name = os.path.splitext(os.path.basename(filename))[0]    
        subfolder_path = os.path.join(os.getcwd(), folder_name)
        os.makedirs(subfolder_path, exist_ok=True)
        file_path = os.path.join(subfolder_path, filename)
            
        with open(file_path, "w", encoding="utf-8") as file:
            for link in titles:
                file.write(link + "\n")
                    
        for playlist_link, playlist_title in zip(urls, titles):
            download_video(playlist_link, subfolder_path, playlist_title)
            convert_audio_to_text(os.path.join(subfolder_path, f"{playlist_title}.mp3"))
        
        merge_text_files(subfolder_path, filename)
    else:
        print("Invalid option")