FROM gorialis/discord.py:minimal

WORKDIR /app
COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . .
ENV PYTHONUNBUFFERED 1

CMD ["python", "bot.py"]
