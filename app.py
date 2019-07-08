import json
import os
import urllib.parse
import sys
import urllib.request
import time
from datetime import *
import psycopg2
import requests
from psycopg2 import sql

from urllib.parse import urlencode
from urllib.request import Request, urlopen

from flask import Flask, request

app = Flask(__name__)


@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()
    log('Recieved {}'.format(data))
    # We don't want to reply to ourselves
    if data['name'] != 'WORKOUT BOT' and data['name'] != 'TEST':
        GYM_POINTS = 1.0
        TRACK_POINTS = 1.0
        THROW_POINTS = 0.5
        SWIM_POINTS = 1.0
        PICKUP_POINTS = 0.5
        BIKING_POINTS = 1.0
        try:
            # set up connection to the database
            urllib.parse.uses_netloc.append("postgres")
            url = urllib.parse.urlparse(os.environ["DATABASE_URL"])
            conn = psycopg2.connect(
                database=url.path[1:],
                user=url.username,
                password=url.password,
                host=url.hostname,
                port=url.port
            )
            cursor = conn.cursor()
            # add 1 to the number of posts of the person that posted
            cursor.execute(sql.SQL(
                "UPDATE tribe_data SET num_posts = num_posts+1 WHERE id = %s"),
                (data['user_id'],))
            if cursor.rowcount == 0:  # No id but possibly has a name
                cursor.execute(sql.SQL(
                    "UPDATE tribe_data SET num_posts = num_posts+1, id = %s WHERE name = %s"),
                    (data['user_id'], data['name'],))
                send_debug_message("gave an id to %s" % data['name'])
            if cursor.rowcount == 0:  # Is not present in the database and needs to be added
                cursor.execute(sql.SQL("INSERT INTO tribe_data VALUES (%s, 1, 0, 0, now(), %s)"),
                               (data['name'], data['user_id'],))
                send_debug_message("added %s to the group" % data['name'])
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as error:
            send_debug_message(error)
        text = data['text'].lower()
        if '!website' in text:
            # send the website information to the groupme
            send_tribe_message("https://gttribe.wordpress.com/about/")
        if '!iloveyou' in text:
            # special command for Stephen Mock
            send_tribe_message("I love you too %s <3" % data['name'])
        if '!help' in text:
            # Special command for Jeffrey Minowa
            send_tribe_message(
                "available commands: !throw, !gym, !swim, !track, !bike, !pickup, !website, !leaderboard, !workouts, !talkative, !points, !ratio, !heatcheck")
        #    send_tribe_message("url: http://www.ultianalytics.com/app/#/5629819115012096/login || password: %s" % (os.getenv("ULTI_PASS")))
        if '!points' in text:
            send_tribe_message("Track: %.1f, Gym: %.1f, Throw: %.1f, Swim: %.1f, Pickup: %.1f, Biking: %.1f" % (
            TRACK_POINTS, GYM_POINTS, THROW_POINTS, SWIM_POINTS, PICKUP_POINTS, BIKING_POINTS))
        if '!gym' in text:
            handle_workouts(data, GYM_POINTS)
        if '!throw' in text:
            handle_workouts(data, THROW_POINTS)
        if '!swim' in text:
            handle_workouts(data, SWIM_POINTS)
        if '!track' in text:
            handle_workouts(data, TRACK_POINTS)
        if '!bike' in text:
            handle_workouts(data, BIKING_POINTS)
        if '!pickup' in text:
            handle_workouts(data, PICKUP_POINTS)
        if '!leaderboard' in text:  # post the leaderboard in the groupme
            print_stats(3, True)
        if '!workouts' in text:  # display the leaderboard for who works out the most
            print_stats(2, True)
        if '!talkative' in text:  # displays the leaderboard for who posts the most
            print_stats(1, True)
        if '!handsome' in text:  # displays the leaderboard for who posts the most
            print_stats(1, True)
        if '!heatcheck' in text:
            send_tribe_message("Kenta wins")
        if '!hydrate' in text:
            add_hydration(data, 1)
        if '!waterboard' in text:
            print_water()
        if '!stackbread' in text:
            send_tribe_message("This is dumb.")
        if '!ratio' in text:
            try:
                urllib.parse.uses_netloc.append("postgres")
                url = urllib.parse.urlparse(os.environ["DATABASE_URL"])
                conn = psycopg2.connect(
                    database=url.path[1:],
                    user=url.username,
                    password=url.password,
                    host=url.hostname,
                    port=url.port
                )
                cursor = conn.cursor()
                # get all of the people who's workout scores are greater than -1 (any non players have a workout score of -1)
                cursor.execute(sql.SQL(
                    "SELECT * FROM tribe_data WHERE workout_score > -1.0"), )
                leaderboard = cursor.fetchall()
                new_leaderboard = []
                for person in leaderboard:
                    if person[2] == 0:
                        ratio = 0
                    else:
                        ratio = person[3] / person[2]
                    new_leaderboard.append((person[0], ratio))
                new_leaderboard.sort(key=lambda s: s[1], reverse=True)  # sort the leaderboard by score descending
                string1 = "Top 15:\n"
                string2 = "Everyone Else:\n"
                for x in range(0, 15):
                    string1 += '%d) %s - %.2f \n' % (x + 1, new_leaderboard[x][0], new_leaderboard[x][1])
                for x in range(15, len(leaderboard)):
                    string2 += '%d) %s - %.2f \n' % (x + 1, new_leaderboard[x][0], new_leaderboard[x][1])
                # need to split it up into 2 because groupme has a max message length for bots
                send_tribe_message(string1)
                send_tribe_message(string2)
                cursor.close()
                conn.close()
            except (Exception, psycopg2.DatabaseError) as error:
                send_debug_message(error)
        if '!reset' in text and data['name'] == 'William Syre':
            send_tribe_message("Final leaderboard is:")
            print_stats(3, True)
            try:
                urllib.parse.uses_netloc.append("postgres")
                url = urllib.parse.urlparse(os.environ["DATABASE_URL"])
                conn = psycopg2.connect(
                    database=url.path[1:],
                    user=url.username,
                    password=url.password,
                    host=url.hostname,
                    port=url.port
                )
                cursor = conn.cursor()
                # add 1 to the number of posts of the person that posted
                cursor.execute(sql.SQL(
                    "UPDATE tribe_data SET workout_score = 0, num_workouts = 0, last_post = now() WHERE workout_score > -1"))
                conn.commit()
                cursor.close()
                conn.close()
                send_debug_message("workouts have been purged")
            except Exception as error:
                send_debug_message(error)
        if 'bamasecs' in text:
            send_tribe_message("Fuck Bama Secs")
        if '!fix' in text:
            seql = data['text'][5:]
            try:
                urllib.parse.uses_netloc.append("postgres")
                url = urllib.parse.urlparse(os.environ["DATABASE_URL"])
                conn = psycopg2.connect(
                    database=url.path[1:],
                    user=url.username,
                    password=url.password,
                    host=url.hostname,
                    port=url.port
                )
                cursor = conn.cursor()
                # add 1 to the number of posts of the person that posted
                cursor.execute(sql.SQL(str(seql)))
                conn.commit()
                cursor.close()
                conn.close()
                send_debug_message(seql)
            except Exception as error:
                send_debug_message(error)
        if '!regionals' in text:
            now = datetime.now()
            regionals = datetime(2019, 4, 28, 8, 0, 0)
            until = regionals - now
            send_tribe_message("regionals is in " + stringFromSeconds(until.total_seconds()))
    return "ok", 200


def send_tribe_message(msg):
    send_message(msg, os.getenv("TRIBE_BOT_ID"))


def handle_workouts(data, addition):
    if len(data['attachments']) > 0:
        # attachments are images or @mentions
        group_members = get_group_info(data['group_id'])  # should get the groupme names of all members in the group.
        names, ids = get_names_and_ids_from_message(data, True)
        if names is not None and ids is not None:
            num = add_to_db(names, addition, ids)
        if num == len(names):
            like_message(data['group_id'], data['id'])


def print_stats(datafield, rev):
    try:
        urllib.parse.uses_netloc.append("postgres")
        url = urllib.parse.urlparse(os.environ["DATABASE_URL"])
        conn = psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )
        cursor = conn.cursor()
        # get all of the people who's workout scores are greater than -1 (any non players have a workout score of -1)
        cursor.execute(sql.SQL(
            "SELECT * FROM tribe_data WHERE workout_score > -1.0"), )
        leaderboard = cursor.fetchall()
        leaderboard.sort(key=lambda s: s[datafield], reverse=rev)  # sort the leaderboard by score descending
        string1 = "Top 15:\n"
        string2 = "Everyone Else:\n"
        for x in range(0, 15):
            string1 += '%d) %s with %.1f points \n' % (x + 1, leaderboard[x][0], leaderboard[x][datafield])
        for x in range(15, len(leaderboard)):
            string2 += '%d) %s with %.1f points \n' % (x + 1, leaderboard[x][0], leaderboard[x][datafield])
        send_tribe_message(string1)  # need to split it up into 2 because groupme has a max message length for bots
        send_tribe_message(string2)
        cursor.close()
        conn.close()
    except (Exception, psycopg2.DatabaseError) as error:
        send_debug_message(error)


def send_message(msg, bot_ID):
    url = 'https://api.groupme.com/v3/bots/post'

    data = {
        'bot_id': bot_ID,
        'text': msg,
    }
    request = Request(url, urlencode(data).encode())
    json = urlopen(request).read().decode()


def send_workout_selfie(msg, image_url):
    send_message(msg, os.getenv("WORKOUT_BOT_ID"))
    send_message(image_url, os.getenv("WORKOUT_BOT_ID"))


def send_debug_message(msg):
    send_message(msg, os.getenv("TEST_BOT_ID"))


def log(msg):
    print(str(msg))
    sys.stdout.flush()


def get_group_info(group_id):
    with urllib.request.urlopen("https://api.groupme.com/v3/groups/%s?token=%s" % (
            group_id, os.getenv("ACCESS_TOKEN"))) as response:
        html = response.read()
    dict = parse_group_for_members(html)
    return dict["response"]["members"]


def parse_group_for_members(html_string):
    return json.loads(html_string)


def like_message(group_id, msg_id):
    # send_debug_message("group_id is %s" % str(group_id))
    # send_debug_message("message_id is %s" % str(msg_id))
    url = 'https://api.groupme.com/v3/messages/%s/%s/like?token=%s' % (str(group_id), str(msg_id), os.getenv("ACCESS_TOKEN"))
    data = {}
    requests.post(url, data)


def add_to_db(names, addition, ids):  # add "addition" to each of the "names" in the db
    cursor = None
    conn = None
    num_committed = 0
    try:
        urllib.parse.uses_netloc.append("postgres")
        url = urllib.parse.urlparse(os.environ["DATABASE_URL"])
        conn = psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )
        cursor = conn.cursor()
        for x in range(0, len(names)):
            cursor.execute(sql.SQL(
                "SELECT workout_score FROM tribe_data WHERE id = %s"), (str(ids[x]),))
            score = cursor.fetchall()[0][0]
            score = int(score)
            if score != -1:
                cursor.execute(sql.SQL(
                    "UPDATE tribe_data SET num_workouts = num_workouts+1, workout_score = workout_score+%s, last_post = "
                    "now() WHERE id = %s"),
                    (str(addition), ids[x],))
                if cursor.rowcount == 0:  # If a user does not have an id yet
                    cursor.execute(sql.SQL(
                        "UPDATE tribe_data SET num_workouts = num_workouts+1, workout_score = workout_score+%s, last_post "
                        "= now(), id = %s WHERE name = %s"),
                        (str(addition), names[x], ids[x],))
                    send_debug_message("%s does not have an id yet" % names[x])
                conn.commit()
                send_debug_message("committed %s" % names[x])
                num_committed += 1
            else:
                send_debug_message("invalid workout poster found " + str(score))
    except (Exception, psycopg2.DatabaseError) as error:
        send_debug_message(str(error))
    finally:
        if cursor is not None:
            cursor.close()
            conn.close()
        return num_committed


def add_hydration(data, addition):
    cursor = None
    conn = None
    num_committed = 0
    names, ids = get_names_and_ids_from_message(data, True)
    try:
        urllib.parse.uses_netloc.append("postgres")
        url = urllib.parse.urlparse(os.environ["DATABASE_URL"])
        conn = psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )
        cursor = conn.cursor()
        for x in range(0, len(names)):
            cursor.execute(sql.SQL(
                "UPDATE tribe_water SET num_liters = num_liters+%s WHERE id = %s"),
                (str(addition), ids[x],))
            if cursor.rowcount == 0:  # If a user does not have an id yet
                cursor.execute(sql.SQL(
                    "UPDATE tribe_water SET num_liters = num_liters+%s, id = %s WHERE name = %s"),
                    (str(addition), ids[x], names[x],))
                send_debug_message("%s does not have an id yet" % names[x])
            if cursor.rowcount == 0:  # user is not in the db yet
                cursor.execute(sql.SQL("INSERT INTO tribe_water VALUES (%s, 1, %s)"), (names[x], ids[x],))
            conn.commit()
            send_debug_message("committed %s" % names[x])
            num_committed += 1
    except (Exception, psycopg2.DatabaseError) as error:
        send_debug_message(str(error))
    finally:
        if cursor is not None:
            cursor.close()
            conn.close()
        if len(names) == num_committed:
            like_message(data['group_id'], data['id'])
        return num_committed


def get_names_and_ids_from_message(data, require_attachment):
    if len(data['attachments']) > 0:
        # attachments are images or @mentions
        ids = []
        group_members = get_group_info(data['group_id'])  # should get the groupme names of all members in the group.
        names = []
        found_attachment = not require_attachment  # This will track whether we found an image or not, which is required
        for attachment in data["attachments"]:
            if attachment['type'] == 'image':
                found_attachment = True
            if attachment['type'] == 'mentions':  # grab all the people @'d in the post to include them
                send_debug_message(str(attachment['user_ids']))
                for mentioned in attachment['user_ids']:
                    for member in group_members:
                        if member["user_id"] == mentioned:
                            names.append(member["nickname"])
                            ids.append(member["user_id"])
        if found_attachment:  # return all mentions plus the name of the poster
            names.append(data['name'])
            ids.append(data['user_id'])
            return names, ids
        else:
            return None, None


def print_water():
    try:
        urllib.parse.uses_netloc.append("postgres")
        url = urllib.parse.urlparse(os.environ["DATABASE_URL"])
        conn = psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )
        cursor = conn.cursor()
        # get all of the people who's workout scores are greater than -1 (any non players have a workout score of -1)
        cursor.execute(sql.SQL(
            "SELECT * FROM tribe_water WHERE num_liters > -1.0"), )
        leaderboard = cursor.fetchall()
        leaderboard.sort(key=lambda s: s[1], reverse=True)  # sort the leaderboard by score descending
        string1 = "Top 15:\n"
        string2 = "Everyone Else:\n"
        for x in range(0, 15):
            if x < len(leaderboard):
                string1 += '%d) %s with %d points \n' % (x + 1, leaderboard[x][0], leaderboard[x][1])
        if len(leaderboard) > 15:
            for x in range(15, len(leaderboard)):
                string2 += '%d) %s with %d points \n' % (x + 1, leaderboard[x][0], leaderboard[x][1])
        send_tribe_message(string1)  # need to split it up into 2 because groupme has a max message length for bots
        if len(leaderboard) > 15:
            send_tribe_message(string2)
        cursor.close()
        conn.close()
    except (Exception, psycopg2.DatabaseError) as error:
        send_debug_message(error)


def send_direct_message(user_id, text):
    url = r"https://api.groupme.com/v3/direct_messages?token=%s" % (os.getenv("APP_ACCESS_TOKEN"))
    data = {'direct_message': {
        'source_guid': str(time.time()),
        'recipient_id': str(user_id),
        'conversation_id': "%s+16458398" % str(user_id),
        'text': text
        }
    }
    try:
        params = json.dumps(data).encode('utf8')
        request = Request(url, data=params, headers={'content-type': 'application/json'})
        response = urlopen(request).read().decode()
    except Exception as error:
        send_debug_message(str(error))

def stringFromSeconds(seconds):
    if seconds < 0:
        return seconds, " seconds. You missed it, better luck next year."
    else:
        days = seconds / 60 / 60 / 24
        fracDays = days - int(days)
        hours = fracDays * 24
        fracHours = hours - int(hours)
        minutes = fracHours * 60
        fracMinutes = minutes - int(minutes)
        seconds = fracMinutes * 60
        return "%d days, %d hours, %d minutes, %d seconds" % (days, minutes, hours, seconds)
