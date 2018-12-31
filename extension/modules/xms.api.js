export default class xmsClient {
    constructor(apiUrl) {
        this.xmsAPIAuthToken = null;
        this.xmsApiUrl = apiUrl; //https://xms.dev.elwood.systems/api';

        try {
            console.log("Getting Auth Token from XMS API");

            this.getLatestAuthorizationKey()
                .then((token) => {
                    //console.log('Auth token response = ' + token)
                    this.xmsAPIAuthToken = token
                    //console.log('XMS Auth Token = ' + this.xmsAPIAuthToken)
                })
                .catch(function (err) {
                    console.log('Failed to get token')
                    console.table(err)
                })
        } catch (error) {
            console.log("Error getting auth token " + error);
        }
    }


    getLatestAuthorizationKey() {
        const oauthApplicationId = 'aus2eaqpr0kZ9gg2f0i7';
        const oktaOAuthEndpoint = 'https://elwoodam.okta-emea.com/oauth2/' + oauthApplicationId + '/v1/token';
        var authHeaders = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cache-Control': 'no-cache'
        }
        var data = {
            grant_type: 'client_credentials',
            client_id: '0oa2eauwer5y529M40i7',
            client_secret: 'XbqpNLN6DcUkiD1opm_4a7FMJKECV-JlyleT31yM'
        }
        var authToken = null;

        var query = ''
        for (var key in data) {
            query += encodeURIComponent(key) + "=" + encodeURIComponent(data[key]) + "&";
        }

        return new Promise((resolve, reject) => {
            fetch(oktaOAuthEndpoint, {
            method: 'POST',
            headers: authHeaders,
            body: query
            })
            .then(res => res.json())
            .then(response => {
                authToken = response.access_token
                resolve(authToken);
            })
            .catch(function (error) {
                console.log(error)
                reject(error)
            })
        })
    }

    sendOrder(quantity, price, tag) {
        const xmsOrderEndpoint = this.xmsApiUrl + '/order';
        var authHeaders = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Cache-Control': 'no-cache',
            'X-Api-Authorization': 'Bearer ' + this.xmsAPIAuthToken
        }

        var orderData = {
            "side": "BUY",
            "security_id_source": "ID",
            "security_id": "6070",
            "quantity": quantity,
            "order_type": "LIMIT",
            "limit_price": price,
            "timeinforce": "GOOD_TILL_CANCEL",
            "props": {},
            "account_id": 0,
            "tag": tag,
            "source": "nico_api",
            "market_connector": "bitmex"
        }

        return new Promise((resolve, reject) => {
            fetch(xmsOrderEndpoint, {
                method: 'POST',
                headers: authHeaders,
                body: JSON.stringify(orderData)
            })
            .then(res => {
                if (res.status >= 200 && res.status < 400) {
                    resolve(res)
                } else {
                    reject(res)
                }
            })
            .catch(function (error) {
                console.log(error)
                reject(error)
            })
        })
    }

    getInstrument(symbol, exchange) {
        var authHeaders = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Cache-Control': 'no-cache',
            'X-Api-Authorization': 'Bearer ' + this.xmsAPIAuthToken
        }

        var query = ''
        query += "symbol=" + encodeURIComponent(symbol) + "&";
        query += "exchange_id=" + encodeURIComponent(exchange)
        
        var xmsInstrumentRequestUrl = this.xmsApiUrl + '/instrument?' + query;

        return new Promise((resolve, reject) => {
            fetch(xmsInstrumentRequestUrl, {
                method: 'GET',
                headers: authHeaders
            })
            .then(res => {
                if (res.status >= 200 && res.status < 400) {
                    resolve(res)
                } else {
                    reject(res)
                }
            })
            .catch(function (error) {
                console.log(error)
                reject(error)
            })
        })
    }
}