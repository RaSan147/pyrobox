class Error_Page {
	constructor() {
		this.type = "error"

		this.my_part = document.getElementById("error-page")
	}

	initialize() {
		page.hide_actions_button(); // Hide actions button, not needed 
		page.set_title("Error")
	}

	hide() {
		this.my_part.classList.remove("active");
	}

	show() {
		this.my_part.classList.add("active");
	}

	clear() {
	}
}

var error_page = new Error_Page()