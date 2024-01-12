from django.shortcuts import render
from .models import Chat, ChatFavorite, Assistant, Thread
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import requests
import json
import re
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from urllib.parse import unquote

SESSION_CHAT_ID = 'chat_id'

def cleanup_openai_text(text):
    return re.sub(r'【.*?】', '', text)

def get_openai_headers():
    headers = {
      "Content-Type": "application/json",
      'OpenAI-Beta': "assistants=v1",
      'Authorization': f"Bearer {settings.OPENAI_API_KEY}"
    }
    return headers

def chat_check_status(request):
    result = {
        'status': None,
        'msg': 'unknown',
        'run_id': None,
    }
    current_chat_id = request.session.get(SESSION_CHAT_ID)
    if current_chat_id is not None:
        try:
            chat = Chat.objects.get(pk=current_chat_id)
            thread_id = chat.thread.openai_id
            run_id = chat.openai_id
            endpoint = f"https://api.openai.com/v1/threads/{thread_id}/runs/{run_id}"
            r = requests.get(endpoint, headers=get_openai_headers())
            openai_data = json.loads(r.text)
            chat.status = openai_data['status']
            chat.save()
            result['status'] = chat.status
            if openai_data['status'] == 'queued':
                result['msg'] = 'Waiting...'
            if openai_data['status'] == 'in_progress':
                result['msg'] = 'Working...'
            if openai_data['status'] == 'completed':
                result['msg'] = 'Done'
                endpoint = f"https://api.openai.com/v1/threads/{thread_id}/messages"
                r = requests.get(endpoint, headers=get_openai_headers())
                openai_data = json.loads(r.text)
                msg0 = openai_data['data'][0]              
                assert(msg0['content'][0]['type'] == 'text')

        except Chat.DoesNotExist as exc:
            pass
    data = json.dumps(result)
    return HttpResponse(data, content_type='application/json')

def test_view(request):
    #messages.info(request, "Three credits remain in your account.")
    #foo = ChatFavorite.normalize_rank()
    has_permission = True
    response = render(request, 'test.html', locals())
    return response

def chat(request):
    has_permission = request.user.is_authenticated
    if request.method == 'GET':
        chat = None
        current_chat_id = request.session.get(SESSION_CHAT_ID)
        if current_chat_id is not None:
            try:
                chat = Chat.objects.get(pk=current_chat_id)
            except Chat.DoesNotExist as exc:
                pass
        if chat is None:
            chat = Chat()
            chat.save()
            current_chat_id = chat.id
            request.session[SESSION_CHAT_ID] = current_chat_id
        thrd = chat.thread
        if thrd is None:
            thrd = Thread()
            thrd.save()
            chat.thread = thrd
            chat.save()
        if thrd.openai_id is None:
            # Need to create openai thread
            endpoint = 'https://api.openai.com/v1/threads'
            r = requests.post(endpoint, headers=get_openai_headers())
            if r.status_code == 200:
                openai_data = json.loads(r.text)
                thrd.openai_id = openai_data['id']
                thrd.created_at = datetime.utcfromtimestamp(openai_data['created_at'])
                thrd.save()
        msgs_thread = thrd.get_messages()
        m = msgs_thread['data']
        m2 = m.copy()
        m2.reverse()
        msgs = [{'role': m['role'], 'content': cleanup_openai_text(m['content'][0]['text']['value'])} for m in m2]
        chat.msgs = json.dumps(msgs)
        chat.save()
        chat_resp = render(request, 'chat-turn.html', locals())
        return chat_resp
    elif request.method == 'POST':
        if request.POST['chat_action'] == 'new_chat':
            request.session[SESSION_CHAT_ID] = None
        elif request.POST['chat_action'] == 'submit':
            chat = None
            current_chat_id = request.session.get(SESSION_CHAT_ID)
            assert(current_chat_id is not None)
            try:
                chat = Chat.objects.get(pk=current_chat_id)
            except Exception:
                request.session[SESSION_CHAT_ID] = None
                resp = HttpResponseRedirect('/chat/')
                return resp
            msg_content = request.POST['user_msg'].strip()
            if len(msg_content) > 0:
                # Add message to thread
                thrd = chat.thread
                if thrd is None:
                    thrd = Thread()
                    thrd.save()
                    chat.thread = thrd
                    chat.save()
                if thrd.openai_id is None:
                    # Need to create openai thread
                    endpoint = 'https://api.openai.com/v1/threads'
                    r = requests.post(endpoint, headers=get_openai_headers())
                    if r.status_code == 200:
                        openai_data = json.loads(r.text)
                        thrd.openai_id = openai_data['id']
                        thrd.created_at = datetime.utcfromtimestamp(openai_data['created_at'])
                        thrd.save()
                endpoint = f'https://api.openai.com/v1/threads/{thrd.openai_id}/messages'
                data = {'role': Chat.USER_ROLE, 'content': msg_content}
                r = requests.post(endpoint, headers=get_openai_headers(), data=json.dumps(data))
                endpoint = f'https://api.openai.com/v1/threads/{thrd.openai_id}/runs'
                data = {'assistant_id': Assistant.ASSISTANT_ID}
                r = requests.post(endpoint, headers=get_openai_headers(), data=json.dumps(data))                
                if r.status_code == 200:
                    data = json.loads(r.text)
                    run_id = data['id']
                    chat.openai_id = run_id
                    chat.status = data['status']
                    chat.save()
        elif request.POST['chat_action'] == 'cancel':
            pass #TODO: FIX THIS

        resp = HttpResponseRedirect('/chat/')
        return resp

@login_required
def chat_show(request, chat_id=None):
    msg_list = []
    msg_str = None
    chat_id_int = int(chat_id) if chat_id is not None else None
    chats = Chat.objects.order_by('created_at')
    chat_list = []
    for chat in chats:
        if len(chat.msgs) == 0:
            continue
        try:
            msgs = json.loads(chat.msgs)
            if type(msgs) == list:
                if chat.id == chat_id_int:
                    msg_list = msgs
                    msg_idx = 0
                    for m in msg_list:
                        m['idx'] = msg_idx
                        msg_idx += 1
                chat_list.append({'id': chat.id, 'title': msgs[0]['content']})
        except Exception as exc:
            pass
    response = render(request, 'chat-show.html', locals())
    return response

def chat_show_action(request):
    post = request.POST
    if 'favorites' in post['chat_action']:
        for p in post.keys():
            if p.startswith('msg-chk-'):
                user_msg_idx = int(p[8:])
                usr_msg = unquote(post[f'msg_str_{user_msg_idx}'])
                assist_msg_idx = user_msg_idx + 1
                assist_msg = unquote(post[f'msg_str_{assist_msg_idx}'])
                fav = ChatFavorite(user_msg=usr_msg, assist_msg=assist_msg)
                fav.save()
        resp = HttpResponseRedirect(f'/chat-show/{post["chat_id"]}')
        return resp
    elif 'delete_chat' in post['chat_action']:
        try:
            Chat.objects.filter(id=int(post['chat_id'])).delete()
        except Chat.DoesNotExist as exc:
            pass
        resp = HttpResponseRedirect('/chat-show/')
        return resp

        pass

    resp = HttpResponseRedirect('/chat-show/')
    return resp

def chat_favs(request):
    favs = ChatFavorite.objects.order_by('-rank')
    response = render(request, 'chat-favs.html', locals())
    return response

def about_morgan(request):
    response = render(request, 'about.html', locals())
    return response
