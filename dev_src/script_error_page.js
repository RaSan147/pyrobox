class Error_Page extends Page {
	constructor(controller=page_controller, type="error", handle_part="error-page") {
		super(controller, type, handle_part);
	}

	initialize() {
		this.controller.hide_actions_button(); // Hide actions button, not needed
		this.controller.set_title("Error")
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

page_controller.add_handler("error", Error_Page, "error-page");