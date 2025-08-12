import yaml
import streamlit as st
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from streamlit_authenticator.utilities import (CredentialsError,
                                               ForgotError,
                                               Hasher,
                                               LoginError,
                                               RegisterError,
                                               ResetError,
                                               UpdateError)

# Loading config file
with open('config.yaml', 'r', encoding='utf-8') as file:
    config = yaml.load(file, Loader=SafeLoader)

#stauth.Hasher.hash_passwords(config['credentials'])

#authenticator = stauth.Authenticate(
#    config['credentials'],
#    config['cookie']['name'],
#    config['cookie']['key'],
#    config['cookie']['expiry_days']
#)

#with open('config.yaml', 'w') as file:
#    yaml.dump(config, file, default_flow_style=False, allow_unicode=True)

def login():
    try:
        authenticator = stauth.Authenticate(
            config['credentials'],
            config['cookie']['name'],
            config['cookie']['key'],
            config['cookie']['expiry_days']
        )
        authenticator.login()
    except LoginError as e:
        st.error(e)

    if st.session_state["authentication_status"]:
        authenticator.logout(location="sidebar")
        return True
    elif st.session_state["authentication_status"] is False:
        st.error('Username/password is incorrect')
        return False
    elif st.session_state["authentication_status"] is None:
        return False
    