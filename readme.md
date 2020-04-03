# covid-19

### confirmed cases modeling

Data without science :(

Try modeling number of confirmed cases in each country as CDF of a Gaussian. (Assumption: convergence, Gaussian, time-lagged Korea looks like China.)

Use converged countries to fit the Gaussian then to estimate the onset of ongoing countries.

### other scripts inspired by this particular period

* Amazon Fresh delivery window refresher
  * As of 20200325 Amazon Fresh delivery is often booked out in NY area. Reddit posts seem to suggest delivery window gets posted at midnight. Is that the case? This queries the page (with a valid request from cURL) periodically to find out, and upon finding such window, notify.
  * Delivery windows are indeed released throughout the day, and they are fairly competitive (20200403 seemed to have been significantly more competitive than 20200325). Session expires in about 2 hours.
  * Looking at the request, when replacing cookies, session-id and session-id-time would not change, but session-token would. Other cookie fields, such as "at-main", also do not change, but are mandatory to constitute a complete request. Guessing session-token seems unlikely, and Selenium-based token replacement would probably be the way to go if we were to enhance this.
  * Deployment: `*/5 * * * * cd /Users/zwang/personal/coronavirus/src && /usr/local/bin/python3 ./amazon_refresh.py`
