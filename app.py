from flask import Flask, render_template, request, session, redirect, jsonify, url_for, make_response
from oauth import Oauth
import json
import os
from dotenv import load_dotenv

load_dotenv()
import random

app = Flask(__name__)
app.config["SECRET_KEY"] = f"{os.urandom(24).hex()}"
app.config["DISCORD_CLIENT_ID"] = 970453471453134879
app.config["DISCORD_REDIRECT_URI"] = f"{os.getenv('cur_web')}/login"
app.config["logged in"] = False


@app.route("/")
def home():
    guild_datas = request.cookies.get('guild_datas')
    if guild_datas is not None:
        session["number"] = random.randint(0, 40) % 3
        if session['number'] == 0:
            return redirect(url_for("login"))
    return render_template("index.html", discord_url=Oauth.discord_login_url)

@app.route("/dashboard")
async def redirect_to_login_from_dashboard():
    return redirect(url_for("login"))

@app.route("/login")
async def login():
    try:
        if session['number'] == 0:
            guild_datas = request.cookies.get('guild_datas')
            if guild_datas is not None:
                guild_datas = guild_datas.replace("'", "\"")
                dataa = json.loads(guild_datas)
                data = json.dumps(dataa, indent=4)
                session["loggedin"] = True
                with open("data.json", "w", encoding="UTF8") as f:
                    f.write(data)
                with open("data.json", "r") as f:
                    data = json.load(f)
                return render_template("logged-in.html", guilds=data['0'])
    except KeyError:
        return redirect(url_for("home"))

    code = request.args.get("code")
    at = Oauth.get_access_token(code)
    session["token"] = at
    session["loggedin"] = True

    user_guilds = Oauth.get_user_guilds(at)
    try:
        guild_datas = []
        for guild in user_guilds:
            guildid = guild['id']
            icon = guild['icon']
            guild_name = guild['name'].replace("'", "")
            icon_url = f"https://cdn.discordapp.com/icons/{guildid}/{icon}.png"

            userid = 970453471453134879
            mybot = Oauth.get_user_in_guild(guildid, userid)
            if len(mybot) < 3:
                continue
            else:
                pass

            data = {"i": icon_url, "gd": guildid, "gn": guild_name}
            guild_datas.append(data)

        for guild in user_guilds:
            guildid = guild['id']
            icon = guild['icon']
            guild_name = guild['name'].replace("'", "")
            icon_url = f"https://cdn.discordapp.com/icons/{guildid}/{icon}.png"

            userid = 970453471453134879
            mybot = Oauth.get_user_in_guild(guildid, userid)
            if len(mybot) < 3:
                pass
            else:
                continue

            data = {"i": icon_url, "gd": guildid, "gn": guild_name}
            guild_datas.append(data)

        session['guilddata'] = guild_datas

    except TypeError:
        try:
            guild_datas = session['guilddata']
        except KeyError:
            return redirect(url_for("home"))

    response = make_response(render_template("logged-in.html", guilds=guild_datas))
    response.set_cookie("guild_datas", str({"0": guild_datas}), max_age=60 * 60 * 24 * 2)

    return response


@app.route("/dashboard/<int:guild_id>")
async def dashboard_server(guild_id):
    try:
        prev_url = "/login"
        x = session["loggedin"]
        userid = 970453471453134879
        mybot = Oauth.get_user_in_guild(guild_id, userid)
        if len(mybot) < 3:
            return redirect(
                f'https://discord.com/oauth2/authorize?&client_id={app.config["DISCORD_CLIENT_ID"]}&scope=bot'
                f'&permissions=8&guild_id={guild_id}&response_type=code&'
                f'redirect_uri={app.config["DISCORD_REDIRECT_URI"]}')
        guild_people = Oauth.get_guild_members(guild_id)
        for person in guild_people:
            person_id = person['user']['id']
            tasks = Oauth.get_task(guild_id, person_id)
            person['tasks'] = tasks['tasks']
            guild_people[guild_people.index(person)] = person

        return render_template("render_tasks.html", guild_name=f"{Oauth.get_guild(guild_id)['name']} tasks",
                               members=guild_people, guild_id=guild_id, prev_url=prev_url)
    except KeyError:
        return redirect(url_for("home"))


@app.route("/dashboard/<int:guild_id>/<int:user_id>/tasks", methods=["GET", "POST"])
async def guild_user_assign_task(guild_id, user_id):
    try:
        prev_url = f"/dashboard/{guild_id}"
        x = session["loggedin"]
        if str(request.method) == 'POST':
            task = request.form['task']
            due = request.form['due']
            Oauth.add_task(guild_id, user_id, task, due)
            tasks = Oauth.get_task(guild_id, user_id)
            return render_template("render_user_tasks.html", guild_name=f"{Oauth.get_guild(guild_id)['name']}",
                                   user_name=f"{Oauth.get_user_in_guild(guild_id, user_id)['user']['username']}",
                                   tasks=tasks['tasks'], request=request, user_id=user_id, guild_id=guild_id, prev_url=prev_url)
        elif str(request.method) == "GET":
            tasks = Oauth.get_task(guild_id, user_id)
            return render_template("render_user_tasks.html", guild_name=f"{Oauth.get_guild(guild_id)['name']}",
                                   user_name=f"{Oauth.get_user_in_guild(guild_id, user_id)['user']['username']}",
                                   tasks=tasks['tasks'], request=request, user_id=user_id, guild_id=guild_id, prev_url=prev_url)
    except KeyError:
        return redirect(url_for("home"))


@app.route("/dashboard/<int:guild_id>/<int:user_id>/tasks/complete")
async def guild_user_complete_task(guild_id, user_id):
    try:
        x = check_request_task_and_due(request)
        task = x[0]
        due = x[1]
        Oauth.remove_task(guild_id, user_id, task, due)
        return redirect(url_for("guild_user_assign_task", guild_id=guild_id, user_id=user_id))
    except KeyError:
        return redirect(url_for("home"))


@app.route("/api/v1/gettasks", methods=['GET'])
async def get_tasks():
    e = check_request_id_and_user(request)
    guild_id = e[0]
    user_id = e[1]
    with open("tasks.json", "r") as f:
        data = json.load(f)
        data = data[str(guild_id)][str(user_id)]
    return jsonify(data)


@app.route("/api/v1/removetask", methods=["GET"])
async def remove_task():
    e = check_request_id_and_user(request)
    guild_id = e[0]
    user_id = e[1]
    x = check_request_task_and_due(request)
    got_task = x[0]
    got_due_date = x[1]

    with open("tasks.json", "r") as f:
        data = json.load(f)
        dataa = data[str(guild_id)][str(user_id)]

    tasks = dataa['tasks']
    for task in tasks:
        real_task = task['task']
        due_date = task['due']
        if got_task == real_task and due_date == got_due_date:
            tasks.remove(task)

    data[str(guild_id)][str(user_id)]['tasks'] = tasks
    json_obj = json.dumps(data, indent=4)
    with open("tasks.json", "w") as f:
        f.write(json_obj)

    return jsonify("{'code':'200'}")


@app.route("/api/v1/addtask", methods=["GET"])
async def add_task():
    e = check_request_id_and_user(request)
    guild_id = e[0]
    user_id = e[1]
    x = check_request_task_and_due(request)
    got_task = x[0]
    got_due_date = x[1]
    with open("tasks.json", "r") as f:
        data = json.load(f)
        data[str(guild_id)][str(user_id)]['tasks'].append({"task": f"{got_task}", "due": f"{got_due_date}"})
    json_obj = json.dumps(data, indent=4)
    with open("tasks.json", "w") as f:
        f.write(json_obj)

    return jsonify("{'code':'200'}")


def check_request_task_and_due(request):
    if 'task' in request.args:
        got_task = str(request.args['task'])
    else:
        return "Error: No task field provided. Please specify a task."
    if 'due' in request.args:
        got_due_date = str(request.args['due'])
    else:
        return "Error: No due date field provided. Please specify a due date."
    return (got_task, got_due_date)


def check_request_id_and_user(request):
    if 'guild_id' in request.args:
        guild_id = int(request.args['guild_id'])
    else:
        return "Error: No guild id field provided. Please specify a guild id."
    if 'user_id' in request.args:
        user_id = int(request.args['user_id'])
    else:
        return "Error: No user id field provided. Please specify an user id."
    return (guild_id, user_id)


@app.route("/test")
async def elements_page():
    return render_template("randomthing.html")


if __name__ == "__main__":
    app.run(debug=True)
