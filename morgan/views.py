from django.shortcuts import render
from .models import Chat, ChatFavorite, Assistant, Thread, ChatFlag
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import requests
import json
import re
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from urllib.parse import unquote
import random
import pytz
import openai
import morgan.functions

SESSION_CHAT_ID = 'chat_id'
ASSISTANT_ID = 'assistant_id'

def cleanup_openai_text(text):
    return re.sub(r'【.*?】', '', text)

@csrf_exempt
def chat_flag_submit(request):
    result = {
        'status': None,
    }
    request_data = json.loads(request.body)
    user_txt = request_data['user_txt']
    asst_txt = request_data['asst_txt']
    flag_txt = request_data['flag_txt']
    flag = ChatFlag(user_txt=user_txt, asst_txt= asst_txt, flag_txt=flag_txt, status="new")
    flag.save()
    result['status'] = 'saved'
    data = json.dumps(result)
    return HttpResponse(data, content_type='application/json')

def chat_check_status(request):
    result = {
        'status': None,
        'msg': 'unknown',
        'run_id': None,
    }
    current_chat_id = request.session.get(SESSION_CHAT_ID)
    if current_chat_id is not None:
        try:
            tool_outputs = []
            chat = Chat.objects.get(pk=current_chat_id)
            thrd_qs = Thread.objects.filter(run=chat.id)
            thread_id = thrd_qs[0].openai_id
            run_id = chat.openai_id
            client = openai.OpenAI()
            openai_run = client.beta.threads.runs.retrieve(run_id=run_id, thread_id=thread_id)
            chat.status = openai_run.status
            chat.save()
            result['status'] = chat.status
            if openai_run.status == 'queued':
                result['msg'] = 'Waiting...'
            elif openai_run.status == 'in_progress':
                msg = random.choice(['Working...', 'Thinking...', 'Hmmm...', 'Still working...'])
                result['msg'] = msg
            elif openai_run.status == 'completed':
                result['msg'] = 'Done'
                openai_messages = client.beta.threads.messages.list(thread_id=thread_id)
                msg0 = openai_messages.data[0]              
                assert(msg0.content[0].type == 'text')
            elif openai_run.status == 'requires_action':
                # Note: Multiple tools may be needed; collect the results and submit them
                for tc in openai_run.required_action.submit_tool_outputs.tool_calls:
                    fname = tc.function.name
                    args = json.loads(tc.function.arguments)
                    if fname == 'get_deed_info':
                        info = morgan.functions.get_deed_info(args['real_estate_id'])
                        tool_outputs.append({
                                    "tool_call_id": tc.id,
                                    "output": json.dumps(info),
                                })
                    elif fname == 'get_unit_info':
                        info = morgan.functions.get_unit_info(args['unit'], args['prop'])
                        tool_outputs.append({
                                    "tool_call_id": tc.id,
                                    "output": json.dumps(info),
                                })
                    elif fname == 'is_valid_unit':
                        info = morgan.functions.is_valid_unit(args['unit'])
                        tool_outputs.append({
                                    "tool_call_id": tc.id,
                                    "output": json.dumps(info),
                                })
                    elif fname == 'get_all_units':
                        info = morgan.functions.get_all_units()
                        tool_outputs.append({
                                    "tool_call_id": tc.id,
                                    "output": json.dumps(info),
                                })
                    else:
                        print(f"Function {fname} unknown")
                run = client.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread_id,
                    run_id=run_id,
                    tool_outputs=tool_outputs)
            elif openai_run.status == 'submit_tool_outputs':
                run = client.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread_id,
                    run_id=run_id,
                    tool_outputs=tool_outputs)
        except openai.APIError as exc:
            result['msg'] = str(exc)
            result['status'] = 'completed'
        except Chat.DoesNotExist as exc:
            result['msg'] = str(exc)
            result['status'] = 'completed'
    data = json.dumps(result)
    return HttpResponse(data, content_type='application/json')

def test_view(request):
    #messages.info(request, "Three credits remain in your account.")
    #foo = ChatFavorite.normalize_rank()
    has_permission = True
    import sys
    id = 'asst_4KUzH77OqQKGJKzBc3tsr4uv'
    client = openai.OpenAI()
    x = client.beta.assistants.retrieve(id)
    y = x.model_dump_json()
    print(y)
    syspath = ", ".join(sys.path)

    response = render(request, 'test.html', locals())
    return response

def chat(request):
    if request.method == 'GET':
        try:
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
            thrd_qs =  Thread.objects.filter(run=chat.id)
            if thrd_qs.count() == 0:
                thrd = Thread(run=chat)
                thrd.save()
            else:
                thrd = thrd_qs[0]
            client = openai.OpenAI()
            if thrd.openai_id is None:
                # Need to create openai thread
                openai_thread = client.beta.threads.create()
                thrd.openai_id = openai_thread.id
                thrd.created_at = datetime.utcfromtimestamp(openai_thread.created_at).replace(tzinfo=pytz.utc)
                thrd.save()
            openai_messages = client.beta.threads.messages.list(thread_id=thrd.openai_id)
            print(openai_messages)
            m = openai_messages.data
            #m = msgs_thread['data']
            m2 = m.copy()
            m2.reverse()
            msgs = [{'role': m.role, 'content': cleanup_openai_text(m.content[0].text.value)} for m in m2]
            chat.msgs = json.dumps(msgs)
            chat.save()
        except openai.APIError as exc:
            messages.warn(request, f"OpenAI error: {exc}")
        chat_resp = render(request, 'chat-turn.html', locals())
        return chat_resp
    elif request.method == 'POST':
        if request.POST['chat_action'] == 'new_chat':
            request.session[SESSION_CHAT_ID] = None
        elif request.POST['chat_action'] == 'submit':
            chat = None
            assistant_id = request.session.get(ASSISTANT_ID)
            if assistant_id is None or not request.user.is_staff: # always make anonymous users use the *current* default assistant
                assistant_id = Assistant.DEFAULT_ASSISTANT_ID
                request.session[ASSISTANT_ID] = assistant_id
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
                thrd_qs = Thread.objects.filter(run=chat.id)
                if thrd_qs.count() == 0:
                    thrd = Thread(run = chat)
                    thrd.save()
                    chat.thread = thrd
                    chat.save()
                else:
                    thrd = thrd_qs[0]
                client = openai.OpenAI()
                if thrd.openai_id is None:
                    # Need to create openai thread
                    openai_thread = client.beta.threads.create()
                    thrd.openai_id = openai_thread.id
                    thrd.created_at = datetime.utcfromtimestamp(openai_thread.created_at).replace(tzinfo=pytz.utc)
                    thrd.save()
                openai_message = client.beta.threads.messages.create(thrd.openai_id, role=Chat.USER_ROLE, content=msg_content)
                assistant = Assistant.objects.get(openai_id = assistant_id)
                instr_1 = f"Today is {datetime.now().strftime('%A, %B %d, %Y')}.\n"
                new_instructions = assistant.instructions + instr_1
                openai_run = client.beta.threads.runs.create(thread_id=thrd.openai_id, assistant_id=assistant_id, instructions=new_instructions)
                run_id = openai_run.id
                chat.openai_id = run_id
                chat.status = openai_run.status
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
            if p.startswith('msg-fav-chk-') or p.startswith('msg-faq-chk-'):
                user_msg_idx = int(p[12:])
                usr_msg = unquote(post[f'msg_str_{user_msg_idx}'])
                assist_msg_idx = user_msg_idx + 1
                assist_msg = unquote(post[f'msg_str_{assist_msg_idx}'])
                fav = ChatFavorite(user_msg=usr_msg, assist_msg=assist_msg)
                fav.faq = True if p.startswith('msg-faq-chk-') else False
                fav.fav = True if p.startswith('msg-fav-chk-') else False
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
    favs = ChatFavorite.objects.filter(fav=True).order_by('-rank')
    page_title = 'Favorites'
    response = render(request, 'chat-favs.html', locals())
    return response

def chat_faqs(request):
    favs = ChatFavorite.objects.filter(faq=True).order_by('-rank')
    page_title = 'FAQs'
    response = render(request, 'chat-favs.html', locals())
    return response

def current_assistant(request):
    assistant_id = request.session.get(ASSISTANT_ID)
    if assistant_id is None:
        assistants = Assistant.objects.filter(openai_id__isnull=False)
    else:
        assistants = Assistant.objects.filter(openai_id=assistant_id)
    if len(assistants) >= 1:
        assistant_id = assistants[0].openai_id
        request.session[ASSISTANT_ID] = assistant_id
        return assistants[0]
    return None

def about_morgan(request):
    assistant = current_assistant(request)
    response = render(request, 'about.html', locals())
    return response

def choose_assistant(request):
    if request.method == 'GET':
        assistants = Assistant.objects.all()
        assistant_id = request.session.get(ASSISTANT_ID)
        response = render(request, 'choose-assistant.html', locals())
    elif request.method == 'POST':
        id = request.POST['asst']
        assistant = Assistant.objects.get(id=id)
        request.session[ASSISTANT_ID] = assistant.openai_id
        response = HttpResponseRedirect('/chat')
    return response
