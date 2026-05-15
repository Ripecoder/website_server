import os
import json
import requests
import psycopg
import resend

from urllib.parse import urlparse

from flask import Flask, request, jsonify
from flask_cors import CORS

from flask_mail import Mail, Message

