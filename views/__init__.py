import time
from flask import request, Blueprint, make_response, render_template
from config import appconf
from utils.request import *
from utils.time_fmt import format_time


AliyunDK = Blueprint('main', __name__)

from . import main