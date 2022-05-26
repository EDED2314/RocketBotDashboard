import requests
from dotenv import load_dotenv
import os
import json

load_dotenv()


class Oauth:
    client_id = f"{os.getenv('client_id')}"  # Your Client ID here
    client_secret = f"{os.getenv('client_secret')}"  # Your Client Secret here
    redirect_uri = "http://127.0.0.1:5000/login"
    scope = "identify%20email%20guilds"
    discord_login_url = f"https://discord.com/api/oauth2/authorize?client_id=970453471453134879&redirect_uri=http%3A%2F%2F127.0.0.1%3A5000%2Flogin&response_type=code&scope={scope}"  # Paste the generated Oauth2 link here
    discord_token_url = "https://discord.com/api/oauth2/token"
    discord_api_url = "https://discord.com/api/v10/"
    cur_web = f"{os.getenv('cur_web')}"

    @staticmethod
    def get_access_token(code):
        payload = {
            "client_id": Oauth.client_id,
            "client_secret": Oauth.client_secret,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": Oauth.redirect_uri,
            "scope": Oauth.scope
        }

        access_token = requests.post(url=Oauth.discord_token_url, data=payload).json()
        return access_token.get("access_token")

    @staticmethod
    def get_user_guilds(access_token):
        url = f"{Oauth.discord_api_url}/users/@me/guilds"
        headers = {"Authorization": f"Bearer {access_token}"}

        user_object = requests.get(url=url, headers=headers).json()
        return user_object

    @staticmethod
    def get_user_in_guild(guildid, userid):
        headers = {"Authorization": f"Bot {os.getenv('TOKEN')}"}
        url = f"{Oauth.discord_api_url}/guilds/{guildid}/members/{userid}"
        user_object = requests.get(url=url, headers=headers).json()
        return user_object

    @staticmethod
    def get_guild_members(guildid):
        headers = {"Authorization": f"Bot {os.getenv('TOKEN')}"}
        url = f"{Oauth.discord_api_url}/guilds/{guildid}/members"
        guild_member_obj = requests.get(url=url, headers=headers, params={"limit": "20"}).json()
        return guild_member_obj

    @staticmethod
    def get_guild(guildid):
        headers = {"Authorization": f"Bot {os.getenv('TOKEN')}"}
        url = f"{Oauth.discord_api_url}/guilds/{guildid}"
        guildobj = requests.get(url=url, headers=headers).json()
        return guildobj

    @staticmethod
    def get_user_json(access_token):
        url = f"{Oauth.discord_api_url}/users/@me"
        headers = {"Authorization": f"Bearer {access_token}"}
        user_object = requests.get(url=url, headers=headers).json()
        return user_object

    @staticmethod
    def get_task(guild_id, user_id):
        with open("tasks.json", "r") as f:
            data = json.load(f)
            try:
                data = data[str(guild_id)][str(user_id)]
            except KeyError:
                return {"tasks": []}
            # json_object = json.loads(data)
        return data

    @staticmethod
    def remove_task(guild_id, user_id, taskk, due):
        with open("tasks.json", "r") as f:
            data = json.load(f)
            dataa = data[str(guild_id)][str(user_id)]

        tasks = dataa['tasks']
        for task in tasks:
            real_task = task['task']
            due_date = task['due']
            if taskk == real_task and due_date == due:
                tasks.remove(task)

        data[str(guild_id)][str(user_id)]['tasks'] = tasks
        json_obj = json.dumps(data, indent=4)
        with open("tasks.json", "w") as f:
            f.write(json_obj)

    @staticmethod
    def add_task(guild_id, user_id, task, due):
        with open("tasks.json", "r") as f:
            data = json.load(f)
            try:
                data[str(guild_id)][str(user_id)]['tasks'].append({"task": f"{task}", "due": f"{due}"})
            except KeyError:
                data[str(guild_id)][str(user_id)] = {"tasks": [{"task": f"{task}", "due": f"{due}"}]}
        json_obj = json.dumps(data, indent=4)
        with open("tasks.json", "w") as f:
            f.write(json_obj)
