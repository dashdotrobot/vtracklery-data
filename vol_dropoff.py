#!/usr/bin/env python

'Analyze volunteer drop-off.'

from datetime import datetime
from datetime import timedelta
import numpy as np
import matplotlib.pyplot as pp


def delta_month(d, m):
    'Increment date d by number of months m.'

    next_year, next_month = divmod(d.month+m, 12)
    if next_month == 0:
        next_month = 12
        next_year = next_year - 1

    return datetime(year=d.year+next_year, month=next_month, day=d.day)


def parse_datetime(s):
    'Convert date/time string from VTracklery to datetime object.'

    tmp = s.split()
    return datetime.strptime(tmp[0]+' '+tmp[1], '%Y-%m-%d %H:%M:%S')


# Load workers table
# {id: {name, join_date}}
workers = {}
with open('workers.2016.09.16a.csv') as f:
    for l in f:
        row = l.strip().split(',')
        w_id = int(row[0])
        w_name = row[1]

        w_join_date = parse_datetime(row[6])

        workers[int(row[0])] = {'name': w_name, 'join_date': w_join_date}

# Load hours table
# (worker_id, start, end, duration)
hours = []
with open('hours.2016.09.16a.csv') as f:
    for l in f:
        row = l.strip().split(',')
        w_id = int(row[2])

        time_start = parse_datetime(row[0])

        if row[1]:
            time_end = parse_datetime(row[1])
            duration = (time_end - time_start).total_seconds()

            # Reject records shorter than 10 min or longer than 10 hours
            if duration > 10*60 and duration < 3600*10:
                hours.append((w_id, time_start, time_end, duration))


# histogram of hours and basic stats
if False:
    dur = [h[3]/3600.0 for h in hours]
    pp.figure(1)
    pp.hist(dur, range=[0.0, 10], bins=20)
    pp.xlabel('Hours per shift')
    pp.ylabel('Frequency')

    print 'Mean shift length: ', np.mean(dur)
    print 'Median shift length: ', np.median(dur)


# Find workers with no work record
if False:
    hours_worker_id = [h[0] for h in hours]
    n_no_record = 0
    for w in workers:
        if w not in hours_worker_id:
            n_no_record += 1

    print n_no_record, 'volunteers without a work record.'


# Monthly average hours logged
if False:
    t_start = datetime(year=2008, month=9, day=1)

    months = range(0, 8*12)
    num_visits = []
    num_hours = []
    for m in months:
        t_1 = delta_month(t_start, m)
        t_2 = delta_month(t_start, m+1)

        # Get all work records (starting) during this month
        h_mo = [h for h in hours if h[1] >= t_1 and h[1] < t_2]

        num_visits.append(len(h_mo))
        num_hours.append(sum([h[3] for h in h_mo]) / 3600.0)

    pp.figure(2)
    # pp.plot(months, num_visits)
    pp.plot(months, num_hours)
    pp.xlabel('Month')
    pp.ylabel('Total hours logged in month')


# Find the earliest and latest dates logged by a worker
for w in workers:
    w_hours = [h for h in hours if h[0] == w]

    if w_hours:
        first_shift = min([h[1] for h in w_hours])
        latest_shift = max([h[1] for h in w_hours])
        days_active = (latest_shift - first_shift).days

        workers[w]['first_shift'] = first_shift
        workers[w]['latest_shift'] = latest_shift
        workers[w]['days_active'] = days_active
    else:
        workers[w]['first_shift'] = None
        workers[w]['latest_shift'] = None
        workers[w]['days_active'] = 0


# Consider only workers who joined between these dates
date_start = datetime(year=2008, month=9, day=1)
date_end = datetime(year=2012, month=8, day=31)

wid_cohort = [w for w in workers
              if workers[w]['first_shift'] and
              workers[w]['join_date'] >= date_start and
              workers[w]['join_date'] < date_end]

n_cohort = len(wid_cohort)

print n_cohort, 'volunteers in cohort.'

# Simple survival analysis
# Generate a survival plot, where:
#   the x-axis is the time since join date, and
#   the y-axis is the number of "surviving" volunteers
# "surviving" means having a work date in the future
if False:

    # Calculate survival curve
    days_after_join = np.arange(1*365)
    frac_survived = np.zeros(days_after_join.shape)

    days_active_array = np.array([workers[w]['days_active']
                                  for w in wid_cohort])

    for d in days_after_join:
        frac_survived[d] = float(sum(days_active_array >= d)) / n_cohort

    pp.figure()
    pp.plot(np.array(days_after_join) / 7, np.array(frac_survived)*100)
    pp.xlabel('Weeks after first shift')
    pp.ylabel('Percentage volunteers still involved')

    # Median time involved
    print 'Median time involved', np.median(days_active_array[days_active_array > 7]) / 7

    # Long-time retention rate
    print 'Involved after 1 year:', frac_survived[-1] * 100


# Average activity curve
if False:
    num_weeks = 52
    active_in_week = np.zeros(num_weeks)
    hours_in_week = np.zeros(num_weeks)
    w_active_in_week = np.zeros(num_weeks)
    w_hours_in_week = np.zeros(num_weeks)

    for w in wid_cohort:
        for wk in range(num_weeks):
            wk_start = workers[w]['first_shift'] + timedelta(weeks=wk)
            wk_end = wk_start + timedelta(weeks=1)

            # hours worked in current week
            h_wk = sum([h[3]/3600 for h in hours
                        if h[0] == w and h[1] >= wk_start and h[1] < wk_end])
            w_active_in_week[wk] = 1*(h_wk > 0)
            w_hours_in_week[wk] = h_wk

        active_in_week = active_in_week + w_active_in_week / n_cohort * 100
        hours_in_week = hours_in_week + w_hours_in_week / n_cohort

    pp.figure(1)
    pp.plot(active_in_week)
    pp.title('Active during week')

    pp.figure(2)
    pp.plot(hours_in_week)
    pp.title('Hours per week')

    pp.show()

pp.show()
