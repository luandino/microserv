# microserv
RSOI Lab number 1

App is tries to be some kind of Scorecard
Email address is retrieved from calendar, not more in "me" a Google+.
App works only if Calendar's tasks are in ASCII, no CIRILLIC.
How it works:
a) App query Google API and receives a CODE
b) with that code resquests (POST) Google
c) Receive a token and a refresh token.
d) Query allowed API's with that token
e) Generate HTML and print values (Name, user's photo and today's tasks)
