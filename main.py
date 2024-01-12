#~~~~~~~~~~~~~ IMPORTS ~~~~~~~~~~~~~#
import assemblyai as aai #Imports Assembly AI to convert Speech to Subtitle file
import praw #Imports praw reddit web scraper
from moviepy.editor import * #imports moviepy video file editor
import pysrt #import pysrt to help work with SRT files
from ibm_watson import TextToSpeechV1 #import IMB Watson to convert text to speech
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator #import watson auth method
import creds #import API keys, file is ignored



#~~~~~~~~~~~~~ USER INPUTS ~~~~~~~~~~~~~#
#THESE ARE API KEYS, YOU CAN CHANGE THEM TO YOUR INFORMATION

#From IMB Waton Text to speech solution
WATSONURL = creds.WATSONURLCRED 
WATSONAPIKEY =  creds.WATSONAPIKEYCRED#make this your watson api

#From Assembly AI
aai.settings.api_key = creds.AAISETTINGS

#From Reddit
REDDITCLIENTID = creds.REDDITCLIENTIDCRED   #make this your reddit client
REDDITCLIENTSECRET = creds.REDDITCLIENTSECRETCRED #make this your reddit secret
NUMBEROFPOSTS = 1 #number of posts dont recommend higher than 3 due to IMB limit
SUBREDDITNAME = "AmItheAsshole" #subreddit to take from


#Add an mp4 to the video path and change this to the file name
VIDEOFILE = "" #make this your video file path


#~~~~~~~~~~~~~ METHODS ~~~~~~~~~~~~~#
#This method scrapes reddit using Praw and users reddit API ID's and returns a list of strings which are the stories
def scrape_reddit():
    storyList = []
    story = ""
    reddit = praw.Reddit(
    client_id= REDDITCLIENTID,
    client_secret= REDDITCLIENTSECRET,
    user_agent="Reddit Scraper by smeech",
)
    #Takes info from inputs to parse through number of stories on the Reddit object created by praw, removing new lines and extra chars then adding it to a list and returning
    subreddit_name = SUBREDDITNAME
    num_posts_to_retrieve = NUMBEROFPOSTS
    subreddit = reddit.subreddit(subreddit_name)
    top_posts = subreddit.new(limit=num_posts_to_retrieve)
    for post in top_posts:
        story = (post.title + post.selftext)
        story = [line.replace('\n','') for line in story]
        story = [line.replace("\\",'') for line in story]
        story = ''.join(str(line) for line in story)
        storyList.append(story)
    return(storyList)

#Takes a list of strings as an input and returns 
def generate_text_to_speech_mp3(listOfStories):
    #counts the number of stories generated
    count = 0
    #Authenticates Watson user and creates ttsObject
    authenticatior = IAMAuthenticator(WATSONAPIKEY)
    ttsObject = TextToSpeechV1(authenticator=authenticatior)
    ttsObject.set_service_url(WATSONURL)
    #go through the list of stories and generate mp3 audio files based on the strings.
    for x in range(len(listOfStories)):
        with open ("./audio" + str(x)+ ".mp3", "wb") as audio_file:
            res = ttsObject.synthesize(listOfStories[x], accept="audio/mp3", voice = 'en-US_AllisonExpressive').get_result()
            audio_file.write(res.content)
        #Add to count and return
        count += 1
    return count

#This function generates SRT files using the MP3's generated from generate_text_to_speech_mp3 and Assembly AI's speech to SRT function 
def generate_srt(numStories):
    for x in range(0, numStories):
        transcript = aai.Transcriber().transcribe("audio" + str(x) + ".mp3")
        subtitlesTranscript = transcript.export_subtitles_srt()
        f = open("subtitles" + str(x) + ".srt","a")
        f.write(subtitlesTranscript)
        f.close()

#This function takes the number of stories and generates an array of ints that correspond to the amount of time the mp3 file is
def get_times(numStories):
    l = []
    totalSeconds = 0
    audioDuration = 0
    for x in range(numStories):
        audioclip = AudioFileClip("audio"  + str(x) + ".mp3")
        audioDuration = audioclip.duration
        if(totalSeconds == 0):
            l.append([0, audioDuration])
            totalSeconds += audioDuration
        else:
            l.append([totalSeconds, (totalSeconds+audioDuration)])
            totalSeconds += audioDuration
    return(l)

#This method takes the VIDEOFILE and takes the number of posts as videoQuanitityArray, and a videoLengthArray holding the length of each MP3 file
def create_smaller_clips(videoQuanitityArray, videoLengthArray):
    for x in range(videoQuanitityArray):
        startTime = int(videoLengthArray[x][0])
        endTime = int(videoLengthArray[x][1])
        #Clips master video into the specified lengths based on the getTimes Function
        #Generates new mp4 clip without audio
        current_video = VideoFileClip(VIDEOFILE).subclip(startTime, endTime).without_audio()
        #Takes audio that corresponds with mp4 clip
        current_audio = AudioFileClip("audio" + str(x) + ".mp3")
        new_audioclip = CompositeAudioClip([current_audio])
        #Adds audio to new video clip
        current_video.audio = new_audioclip
        #Generate MP4 file with cut MP4 and AI generated text to speech mp3.
        current_video.write_videofile(("Video" + str(x) + ".mp4"), fps= 25)

#Takes a time and returns it in seconds to help with the get_times function
def time_to_seconds(time_obj):
    return time_obj.hours * 3600 + time_obj.minutes * 60 + time_obj.seconds + time_obj.milliseconds / 1000

#Creates the subtitle as formatted by moviepy to place on the video using built in moviepy functions
def create_subtitles_clips(subtitles, videosize, fontsize = 24, font = "Arial", color = "white", debug = False):
    subtitle_clips = []
    for subtitle in subtitles:
        start_time = time_to_seconds(subtitle.start)
        end_time = time_to_seconds(subtitle.end)
        duration = end_time - start_time
        video_width, video_height = videosize
        text_clip = TextClip(subtitle.text, fontsize = fontsize, font=font, color = color, bg_color="black", size=(video_width*3/4, None), method ='caption').set_start(start_time).set_duration(duration)
        subtitle_x_position = "center"
        subtitle_y_position = video_height*4/5
        text_position = (subtitle_x_position, subtitle_y_position)
        subtitle_clips.append(text_clip.set_position(text_position))
    return subtitle_clips

#Main to run program
def main():
    #generates an int returned from generate_text_to_speech_mp3 which is the number of stories, as well as mp3's generated from scrape reddit
    count = generate_text_to_speech_mp3(scrape_reddit())
    #Generates SRT's based on the files in the path as well as the number of stories
    generate_srt(count)
    #Clips the video based on the count and get_times array
    create_smaller_clips(count, get_times(count))
    #Loops through number of posts to create each video
    for x in range(NUMBEROFPOSTS):
        #Accesses SRT file and mp4 file, and adds _subtitled to the file name
        current_subtitle = pysrt.open("subtitles" + str(x) + ".srt")
        current_video = VideoFileClip("Video"  + str(x) + ".mp4")
        begin, end = ("Video"  + str(x) + ".mp4").split(".mp4")
        outputVideoFile = begin + '_subtitled'+".mp4"
        print ("Output File Name : ", outputVideoFile)
        #Creates the proper functioning subtitle clip
        subtitle_clips = create_subtitles_clips(current_subtitle, current_video.size)
        #Creates a final video adding the current video and subtitle clip
        final_video = CompositeVideoClip([current_video] + subtitle_clips)
        #Writes the final mp4 video with Video, Subtitles and Audio
        final_video.write_videofile(outputVideoFile)

if __name__ == '__main__':
    main()