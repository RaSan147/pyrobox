
class Zip_Page extends Page {
	constructor(controller=page_controller, type="zip", handle_part="zip-page") {
		super(controller, type, handle_part);

		this.message = document.getElementById("zip-prog")
		this.percentage = document.getElementById("zip-perc")
	}

	async initialize() {
		this.controller.hide_actions_button(); // Hide actions button, not needed here

		this.dl_now = false
		this.check_prog = true

		this.prog_timer = null

		let url = tools.add_query_here("zip_id")

		let data = await fetch(url)
			.then(data => { return data.json() })
			.catch(err => { console.error(err) })

		// {
		// 	"status": status,
		// 	"message": message,
		// 	"zid": zid,
		//  "filename": filename
		// }

		let status = data.status
		let message = data.message
		this.zid = data.zid
		this.filename = data.filename

		const that = this

		if (status) {
			this.prog_timer = setInterval(function () {
				that.ping(window.location.pathname + "?zip&zid=" + that.zid + "&progress")
			}, 500)
		} else {
			this.message.innerHTML = "Error";
			this.percentage.innerText = message;
		}


	}

	hide() {
		this.my_part.classList.remove("active");
	}

	show() {
		this.my_part.classList.add("active");
	}

	clear() {
		this.message.innerHTML = ""
		this.percentage.innerText = ""
		this.dl_now = false
		this.check_prog = true
		this.zid = null
		this.filename = null
		if (this.prog_timer) {
			clearTimeout(this.prog_timer)
			this.prog_timer = null
		}
	}


	ping(url) {
		const that = this
		var xhttp = new XMLHttpRequest();
		xhttp.onreadystatechange = function () {
			if (that.dl_now) {
				return
			}
			if (this.readyState == 4 && this.status == 200) {
				// Typical action to be performed when the document is ready:
				//document.getElementById("demo").innerHTML = xhttp.responseText;
				// json of the response
				var resp = tools.safeJSONParse(this.response, ["status", "message"], 5000);
				// console.log(resp)

				if (resp.status == "SUCCESS") {
					that.check_prog = true;
				} else if (resp.status == "DONE") {
					that.message.innerHTML = "Downloading";
					that.percentage.innerText = "";
					that.dl_now = true;
					clearTimeout(that.prog_timer)
					that.run_dl()
				} else if (resp.status == "ERROR") {
					that.message.innerHTML = "Error";
					that.percentage.innerText = resp.message;
					clearTimeout(that.prog_timer)
				} else if (resp.status == "PROGRESS") {
					that.percentage.innerText = resp.message + "%";
				} else {
					that.percentage.innerText = resp.status + ": " + resp.message;
					if (that.prog_timer) {
						clearTimeout(that.prog_timer)
						that.prog_timer = null
					}
				}
			}
		};
		xhttp.open("GET", url, true);
		xhttp.send();
	}


	run_dl() {
		tools.download(window.location.pathname + "?zip&zid=" + this.zid + "&download", this.filename, true)
	}

}

page_controller.add_handler("zip", Zip_Page, "zip-page");