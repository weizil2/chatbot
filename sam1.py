from openai import OpenAI
import streamlit as st
import time
import re  # Import regular expressions

st.title("Hi, I am Sam")
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY7"])
assistant_id = "asst_gJgtOv3AfenpgV6AYiAZggPC"
speed = 50


chatbot_avatar = "https://i0.imgs.ovh/2024/02/18/o1WhJ.png"


# necessary parts for the chatbot
if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id

if "show_thread_id" not in st.session_state:
    st.session_state.show_thread_id = False

if "first_message_sent" not in st.session_state:
    st.session_state.first_message_sent = False

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    avatar_url = None
    if message["role"] == "assistant":
        # Specify the custom avatar URL for the assistant
        avatar_url = chatbot_avatar
    # Use the avatar URL if provided, otherwise, default to None which will use Streamlit's default icon
    with st.chat_message(message["role"], avatar=avatar_url):
        st.markdown(message["content"])

# chatbot text input area
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
# sidebar
local_css("style.css")
# st.sidebar.markdown("#### When you finish the conversation, please copy and paste this conversation to the questionnaire.\n:star: Please do not paste it to the chatbot page")
# st.sidebar.info(st.session_state.thread_id)
# st.sidebar.caption("Please copy this conversation code")

# Typing animation waiting for response
def update_typing_animation(placeholder, current_dots):
    """
    Updates the placeholder with the next stage of the typing animation.

    Args:
    placeholder (streamlit.empty): The placeholder object to update with the animation.
    current_dots (int): Current number of dots in the animation.
    """
    num_dots = (current_dots % 6) + 1  # Cycle through 1 to 3 dots
    placeholder.markdown("typing" + "." * num_dots)
    return num_dots



# Max message; Handling message input and response
min_messages = 20
max_messages = 80  # 10 iterations of conversation (user + assistant)

if len(st.session_state.messages) < max_messages:
    if len(st.session_state.messages) >= min_messages:
        st.sidebar.markdown(
            "### Please feel free to continue your conversation. When you're done, copy and paste this conversation code below back to the [questionnaire]. \n:star: Please do not paste it to the conversation")
        st.sidebar.info(st.session_state.thread_id)
        st.sidebar.markdown ("### Once pasted to the questionnaire, you can safely close this page and go back to complete the rest of the questions. ")
    
    user_input = st.chat_input("")
    if not st.session_state.first_message_sent:
        st.markdown(
            "<img src= " + chatbot_avatar + " width='120'><br>"
            "You can say something like <br>"
            "<span style='color: #8B0000;'> Hi Sam, let's chat! </span><br>"
            "to the chatbox below and start the conversation", unsafe_allow_html=True
        )
    if user_input:
        st.session_state.first_message_sent = True
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant", avatar = chatbot_avatar):
            message_placeholder = st.empty()
            waiting_message = st.empty()  # Create a new placeholder for the waiting message
            dots = 0
#format the response
#erro message------------------------------------------------------------------------------------------------------------------------------#
            def format_response(response):
                """
                Formats the response to handle bullet points and new lines.
                Targets both ordered (e.g., 1., 2.) and unordered (e.g., -, *, •) bullet points.
                """
                # Split the response into lines
                lines = response.split('\n')
                
                formatted_lines = []
                for line in lines:
                    # Check if the line starts with a bullet point (ordered or unordered)
                    if re.match(r'^(\d+\.\s+|[-*•]\s+)', line):
                        formatted_lines.append('\n' + line)
                    else:
                        formatted_lines.append(line)

                # Join the lines back into a single string
                formatted_response = '\n'.join(formatted_lines)

                return formatted_response.strip()

#simultaneous use/internet issues/
            import time
            max_attempts = 2
            attempt = 0
            while attempt < max_attempts:
                try:
                    update_typing_animation(waiting_message, 5)  # Update typing animation
                    # raise Exception("test")
                    message = client.beta.threads.messages.create(thread_id=st.session_state.thread_id,role="user",content=user_input)
                    run = client.beta.threads.runs.create(thread_id=st.session_state.thread_id,assistant_id=assistant_id,)
                    
                    # Wait until run is complete
                    while True:
                        run_status = client.beta.threads.runs.retrieve(thread_id=st.session_state.thread_id,run_id=run.id)
                        if run_status.status == "completed":
                            break
                        dots = update_typing_animation(waiting_message, dots)  # Update typing animation
                        time.sleep(0.3) 
                    # Retrieve and display messages
                    messages = client.beta.threads.messages.list(thread_id=st.session_state.thread_id)
                    full_response = messages.data[0].content[0].text.value
                    full_response = format_response(full_response)  # Format for bullet points
                    chars = list(full_response)
                    # speed = 20  # Display 5 Chinese characters per second
                    delay_per_char = 1.0 / speed
                    displayed_message = ""
                    waiting_message.empty()
                    for char in chars:
                        displayed_message += char
                        message_placeholder.markdown(displayed_message)
                        time.sleep(delay_per_char)  # Wait for calculated delay time
                    break
                except:
                    attempt += 1
                    if attempt < max_attempts:
                        print(f"An error occurred. Retrying in 5 seconds...")
                        time.sleep(5)
                    else:
                        error_message_html = """
                            <div style='display: inline-block; border:2px solid red; padding: 4px; border-radius: 5px; margin-bottom: 20px; color: red;'>
                                <strong>Network error:</strong> Please try again。
                            </div>
                            """
                        full_response = error_message_html
                        waiting_message.empty()
                        message_placeholder.markdown(full_response, unsafe_allow_html=True)

#------------------------------------------------------------------------------------------------------------------------------#


            

# max message reached
            st.session_state.messages.append(
                {"role": "assistant", "content": full_response}
            )


else:
    st.sidebar.markdown(
        "#### When you finish the conversation, please copy and paste this conversation to the questionnaire.\n:star: Please do not paste it to the chatbot page")
    st.sidebar.info(st.session_state.thread_id)
    st.sidebar.caption("Please copy this conversaton code")
    if user_input:= st.chat_input(""):
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant",avatar=chatbot_avatar):
            message_placeholder = st.empty()
            message_placeholder.info(
                "You have reached the maximum round of conversations with Samantha，please copy the thread_id from the side column and paste the thread_id to the textbox below."
            )
    st.chat_input(disabled=True)



#----------------------------------------------
    # Button to copy thread ID
    # if st.button("Copy thread_id"):
    #     st.session_state.show_thread_id = True
    #
    # # When thread ID is shown, update the flag to hide the input box
    # if st.session_state.get('show_thread_id', False):
    #     st.session_state['thread_id_shown'] = True  # Set the flag to hide the input box
    #     st.markdown("#### Thread ID")
    #     st.info(st.session_state.thread_id)
    #     st.caption("Please copy the thread_id。")



#----------------------------------------------
# else:
#     user_input = st.chat_input("How are you？")
#     st.session_state.messages.append({"role": "user", "content": user_input})

#     # with st.chat_message("user"):
#     #     st.markdown(user_input)

#     with st.chat_message("assistant"):
#         message_placeholder = st.empty()
#         message_placeholder.info(
#             "You have reached the maximum round of conversation with Samantha，please click the button thread_id，copy the thread_id。and paste the thread_id to the Qualtrics questionnaire。"
#         )
    

#     if st.button("Copy thread_id"):
#         st.session_state.show_thread_id = True

#     if st.session_state.show_thread_id:
#         st.markdown("#### Thread ID")
#         st.info(st.session_state.thread_id)
#         st.caption("Please copy the thread_id。")




