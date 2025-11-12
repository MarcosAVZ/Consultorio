# main_flet.py
import os
import csv
import datetime as dt
import flet as ft
import actions as ACT
import ui

from ui import make_app
from functools import partial
#from actions import *
from flet import *
from paths import get_paths
from db import init_db
from validators import validar_campos
from pdf_utils import generar_pdf
from backup_drive import can_backup, backup_now



def app_main(page: ft.Page):
    # Setup básico
    paths = get_paths()
    conn, cur = init_db(paths["DB_NAME"])
    # Construye la interfaz y conecta handlers
    make_app(page, conn, cur, paths)


if __name__ == "__main__":
    ft.app(target=app_main)

