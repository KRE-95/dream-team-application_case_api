import pygal
import pytz
from flask import Flask, render_template
import requests
import json
from datetime import datetime
from dateutil import parser
from pygal.style import LightSolarizedStyle

# Feel free to import additional libraries if you like

app = Flask(__name__, static_url_path='/static')

# Paste the API-key you have received as the value for "x-api-key"
headers = {
    "Content-Type": "application/json",
    "Accept": "application/hal+json",
    "x-api-key": ""
}


# Example of function for REST API call to get data from Lime
def get_api_data(headers, url):
    # First call to get first data page from the API
    response = requests.get(url=url,
                            headers=headers,
                            data=None,
                            verify=False)

    # Convert response string into json data and get embedded limeobjects
    json_data = json.loads(response.text)
    limeobjects = json_data.get("_embedded").get("limeobjects")

    # Check for more data pages and get thoose too
    nextpage = json_data.get("_links").get("next")
    while nextpage is not None:
        url = nextpage["href"]
        response = requests.get(url=url,
                                headers=headers,
                                data=None,
                                verify=False)

        json_data = json.loads(response.text)
        limeobjects += json_data.get("_embedded").get("limeobjects")
        nextpage = json_data.get("_links").get("next")

    return limeobjects


# Index page
@app.route('/')
def index():
    return render_template('home.html')


# Example page
@app.route('/example')
def example():
    # Example of API call to get deals
    base_url = "https://api-test.lime-crm.com/api-test/api/v1/limeobject/deal/"
    params = "?_limit=50"
    url = base_url + params
    response_deals = get_api_data(headers=headers, url=url)

    if len(response_deals) > 0:
        return render_template('example.html', deals=response_deals)
    else:
        msg = 'No deals found'
        return render_template('example.html', msg=msg)


# Average deal vale for won deals the last year
@app.route('/average_deal_value_last_year')
def average_deal_value():
    # API call to get all deals with dealstatus of agreement.
    base_url = "https://api-test.lime-crm.com/api-test/api/v1/limeobject/deal/"
    params = "?_limit=50&dealstatus=agreement"
    url = base_url + params
    response_deals = get_api_data(headers=headers, url=url)
    """ Uses python datetime module to calculate the date from one year ago
        filters out any deals closed before the date.
        Have both timezone information and make them both in UTC timezone, easier to compare.
        now and last_year
    """
    # Get the current datetime in UTC
    now = datetime.now(pytz.utc)  # timezone
    # Takes all the deals starting from January 1st of the last year
    last_year = datetime(now.year - 1, 1, 1, tzinfo=pytz.UTC)
    # initialize the total value and count to 0
    total_value = 0
    count = 0
    # loops through each deal in the response_deals list
    for deal in response_deals:
        # Parser the won date and convert it to datetime object
        won_date = parser.parse(deal['closeddate'])  # pareser blir brukt for at
        # Check if the won date is after begning of last year
        if won_date > last_year:
            # Add the deal value to total value and increment the count
            total_value += deal['value']
            count += 1
            # check if any deals is found
    if count <= 0:
        msg = 'No deals found'
        return render_template('average_deal_value.html', msg=msg)
    else:
        # Calculate the average value of deals return it in jinja
        avg_value = total_value / count
        """ Pygal is interactive data visualization tool, that present data though charts
            - bellow it used Pie chart. 
            - Presented & supported on Jinja2 
         """
        # present this in a pie chart using pygal:
        pie_chart = pygal.Pie()
        pie_chart.title = 'Average Deal Value Last Year'
        pie_chart.add('Average Deal', avg_value)
        # passes pie data to jinja2
        pie_data = pie_chart.render_data_uri()

        return render_template('average_deal_value.html', avg_value=avg_value, pie_data=pie_data)


# Number of won deals per month the last year - presented in chart bar - pygal
@app.route('/agreement_deals_per_month_last_year')
def agreed_deals_per_month_last_year():
    base_url = "https://api-test.lime-crm.com/api-test/api/v1/limeobject/deal/"
    params = "?_limit=50&dealstatus=agreement"
    url = base_url + params
    response_deals = get_api_data(headers=headers, url=url)
    # Get the current datetime in UTC
    now = datetime.now(pytz.utc)  # timezone
    last_year = datetime(now.year - 1, 1, 1, tzinfo=pytz.UTC)  # tar med alle mnd
    # Create an empty dictionary to store the counts of the won deals by month
    agreed_won_deals = {}
    # loops through each deal in response_deals list
    for deal in response_deals:
        # Parse the closed date from the deal and convert it to a datetime object
        agreement_date = datetime.strptime(deal['closeddate'], '%Y-%m-%dT%H:%M:%S%z')
        # Check if the agreement date is after the beginging of the last year.
        if agreement_date > last_year:
            # Extract the month name from agreement date
            month = agreement_date.strftime("%B")  # shows the months
            # Increment the count for the month in the "empty" dictionary
            if month in agreed_won_deals:
                agreed_won_deals[month] += 1
            else:
                # or set to 1, if it doesn't exist.
                agreed_won_deals[month] = 1
    # present data - pygal - this a chart bar - using a builtin style :
    # Create the bar chart:
    bar_chart = pygal.Bar(style=LightSolarizedStyle)
    bar_chart.title = 'Won Deals per Month - 2022'
    bar_chart.x_labels = agreed_won_deals.keys()  # self
    bar_chart.add('Deals', agreed_won_deals.values())
    # Render the chart as an SVG string:
    chart_data = bar_chart.render().strip()  # to remove b/n on front-end
    # return the data in jinja2 - show:
    return render_template('agreed_deals_per_month_last_year.html', agreed_deals=agreed_won_deals,
                           chart_data=chart_data)


# The total value of won deals per month the last year - customer by id and there value - table
# url for webpage
@app.route('/total_won_deals_per_customer_last_year')
def won_deals_total_per_customer():  # a function  will go in action when user interact
    base_url = "https://api-test.lime-crm.com/api-test/api/v1/limeobject/deal/"
    params = "?_limit=50&dealstatus=agreement"
    url = base_url + params
    response_deals = get_api_data(headers=headers, url=url)
    """two date time objects '
    now' = represent the current time in UTC 
    last_year = represent the same date one year ago."""
    now = datetime.now(pytz.utc)  # timezone
    last_year = datetime(now.year - 1, 1, 1, tzinfo=pytz.UTC)  # tar med alle mnd
    # empty dictionary list - to store the total value of won deals per customer.
    won_deals_per_customer = {}
    """ Loop/iterate over the deals in the API response,
     and add up the total value of deals won by 
     each customer in the past year."""
    for deal in response_deals:
        closed_date = datetime.strptime(deal['closeddate'], '%Y-%m-%dT%H:%M:%S%z')
        if closed_date > last_year:
            # Note: This code assumes that the deal['company']
            # field contains the ID of a customer.
            customers = deal['company']
            #  If customers already has an entry in dictionary,
            #  the value increment by value of current deal
            if customers in won_deals_per_customer:
                won_deals_per_customer[customers] += deal['value']
            else:
                # otherwise, a new entry  is created with the value of current deal
                won_deals_per_customer[customers] = deal['value']

    return render_template('total_won_deals_per_customer.html',
                           total_won_customer_deals=won_deals_per_customer, )


# doesn't work -
@app.route('/companies_status')
def companies_status():
    # Example of API call to get deals
    base_url = "https://api-test.lime-crm.com/api-test/api/v1/limeobject/company/"
    params = "?_limit=50/buyingstatus=notinterested"
    url = base_url + params
    response_companies = get_api_data(headers=headers, url=url)
    # two date time object - init them both to utc, easier to compare
    now = datetime.now(pytz.utc)  # timezone
    last_year = datetime(now.year - 1, 1, 1, tzinfo=pytz.UTC)
    # empty dict - store the status for each companies
    companies_status_check = {}
    for company in response_companies:
        # Check if the company has a "closeddate" attribute
        # and convert it to a datetime object.
        if 'closeddate' in company:
            closed_date = datetime.strptime(company['closeddate'], '%Y-%m-%dT%H:%M:%S%z')
        else:
            closed_date = None
            # requirements:
        """
         If the company has a closed date within the past year, 
         mark it as "company"
        """
        if closed_date is not None and closed_date > last_year:
            companies_status_check[company['id']] = 'company'
            """
            If the company has a buying status of "notinterested",
            mark it as "notinterested"
            """
        elif 'buyingstatus' in company and company['buyingstatus']['key'] == 'notinterested':
            companies_status_check[company['id']] = 'notinterested'
            """
             If the company has a closed date but it's older than one year,
             mark it as "inactive”.
            """
        elif closed_date is not None:
            companies_status_check[company['id']] = 'inactive'
            """  
            If the company doesn't fall into any of the above categories,
             mark it as a "prospect"
            """
        else:
            companies_status_check[company['id']] = 'prospect'

        return render_template('companies_status.html', cp_status=companies_status_check)


# DEBUGGING

if __name__ == '__main__':
    app.secret_key = 'somethingsecret'
    app.run(debug=True)
