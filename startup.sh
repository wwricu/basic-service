#!/bin/bash
gunicorn main:app -c ./gunicorn.py
