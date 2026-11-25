class Error_Page extends Page {
	constructor(controller=page_controller, type="error", handle_part="error-page") {
		super(controller, type, handle_part);
	}

	initialize() {
		this.controller.hide_actions_button();
		const codeEl = byId("error_code");
		const msgEl = byId("error_message");
		const code = codeEl ? codeEl.innerText.trim() : "";
		const msg = msgEl ? msgEl.innerText.trim() : "Error";
		const titleStr = code ? (code + " - " + msg) : ("Error: " + msg);
		this.controller.set_title(titleStr);
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