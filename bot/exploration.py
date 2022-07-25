from datetime import datetime
from datetime import timedelta

class Exploration:
  def __init__(self, endTime):
    self.end = datetime.strptime(endTime, "%Y-%m-%dT%H:%M:%S.000Z")
    self.reminderInterval = 30

  def get_end_time(self):
    '''
    Returns a datetime format of the exploration timer.
    Note: Return type is not a string but a date
    Database format: 2021-04-07T06:13:29.000Z
    datetime format: 2021-04-07 06:13:29
    '''
    return self.end

  def get_reminder_time(self):
    '''
    Returns a datetime format of the end of the exploration timer,
    but reminderInterval minutes after the end time.
    '''
    return self.end + timedelta(minutes=self.reminderInterval)

  def set_reminder_time(self, minutes):
    '''
    Sets the reminder timer to be x minutes after the exploration ends.
    Negative numbers will make the reminder go off x minutes before the exploration ends.
    '''
    self.reminderInterval = minutes

  def get_reminder_interval(self):
    return self.reminderInterval

  def get_time_remaining(self):
    '''
    Returns the time remaining until the exploration finishes.
    '''
    diff = self.end - datetime.utcnow()
    days, seconds = diff.days, diff.seconds
    hours = (days * 24 + seconds // 3600) % 24
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60

    return "{} days {} hours {} minutes {} seconds".format(days, hours, minutes, seconds)


  def is_done(self):
    '''
    Returns True if the exploration time has passed. 
    '''
    return datetime.utcnow() > self.end


  def __eq__(self, other):
    return self.end == other.end

  def __str__(self):
    if self.is_done():
      return "There is no exploration running at the moment. No timer is running."
    else:
      return "The exploration will finish in {}, on {} UTC".format(self.get_time_remaining(), self.end)