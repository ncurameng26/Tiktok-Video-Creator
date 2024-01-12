import assemblyai as aai
# import pyttsx3
import praw
from moviepy.editor import *
import pysrt
from ibm_watson import TextToSpeechV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import creds

WATSONURL = creds.WATSONURLCRED #DONT CHANGE
WATSONAPIKEY =  creds.WATSONAPIKEYCRED#make this your watson api
aai.settings.api_key = creds.AAISETTINGS
REDDITCLIENTID = creds.REDDITCLIENTIDCRED   #make this your reddit client
REDDITCLIENTSECRET = creds.REDDITCLIENTSECRETCRED #make this your reddit secret
VIDEOFILE = "" #make this your video file path
NUMBEROFPOSTS = 1

def clipMasterVideo(listSize, timeArray):
    for x in range(listSize):
        startTime = int(timeArray[x][0])
        endTime = int(timeArray[x][1])
        current_video = VideoFileClip("mastervideo.mp4").subclip(startTime, endTime).without_audio()
        current_audio = AudioFileClip("audio" + str(x) + ".mp3")
        new_audioclip = CompositeAudioClip([current_audio])
        current_video.audio = new_audioclip
        current_video.write_videofile(("Video" + str(x) + ".mp4"), fps= 25)

def getTimes(listSize):
    l = []
    totalSeconds = 0
    audioDuration = 0
    for x in range(listSize):
        audioclip = AudioFileClip("audio"  + str(x) + ".mp3")
        audioDuration = audioclip.duration
        if(totalSeconds == 0):
            l.append([0, audioDuration])
            totalSeconds += audioDuration
        else:
            l.append([totalSeconds, (totalSeconds+audioDuration)])
            totalSeconds += audioDuration
    return(l)

def transcriberTool(listSize):
    for x in range(0, listSize):
        transcript = aai.Transcriber().transcribe("audio" + str(x) + ".mp3")
        subtitlesTranscript = transcript.export_subtitles_srt()
        f = open("subtitles" + str(x) + ".srt","a")
        f.write(subtitlesTranscript)
        f.close()


def redditScrape():
    storyList = []
    story = ""
    reddit = praw.Reddit(
    client_id= REDDITCLIENTID,
    client_secret= REDDITCLIENTSECRET,
    user_agent="Reddit Scraper by smeech",
)
    subreddit_name = "AmItheAsshole"
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

# def tts(message):
#     count = 0
#     engine = pyttsx3.init()
#     voices = engine.getProperty('voices') 
#     engine.setProperty('voice', voices[2].id)
#     # engine.say(message)    
#     for x in range(len(message)):
#         engine.save_to_file(message[x], "redditVoice" + str(x) + ".mp4", name= None)
#         engine.runAndWait()
#         count += 1
#     return count

def newtts(message):
    count = 0
    authenticatior = IAMAuthenticator(WATSONAPIKEY)
    newttsObj = TextToSpeechV1(authenticator=authenticatior)
    newttsObj.set_service_url(WATSONURL)
    for x in range(len(message)):
        with open ("./audio" + str(x)+ ".mp3", "wb") as audio_file:
            res = newttsObj.synthesize(message[x], accept="audio/mp3", voice = 'en-US_AllisonExpressive').get_result()
            audio_file.write(res.content)
        count += 1
    return count



def time_to_seconds(time_obj):
    return time_obj.hours * 3600 + time_obj.minutes * 60 + time_obj.seconds + time_obj.milliseconds / 1000

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

def main():
    # print(redditScrape())
    count = newtts(redditScrape())
    transcriberTool(count)
    clipMasterVideo(count, getTimes(count))
    for x in range(NUMBEROFPOSTS):
        current_subtitle = pysrt.open("subtitles" + str(x) + ".srt")
        current_video = VideoFileClip("Video"  + str(x) + ".mp4")
        begin, end = ("Video"  + str(x) + ".mp4").split(".mp4")
        outputVideoFile = begin + '_subtitled'+".mp4"
        print ("Output File Name : ", outputVideoFile)
        subtitle_clips = create_subtitles_clips(current_subtitle, current_video.size)
        final_video = CompositeVideoClip([current_video] + subtitle_clips)
        final_video.write_videofile(outputVideoFile)
    #     #add the audio back

if __name__ == '__main__':
    main()