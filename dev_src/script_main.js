


class ContextMenu {
	constructor() {
		this.old_name = null;
	}
	async on_result(self) {
		var data = false;
		if (self.status == 200) {
			data = tools.safeJSONParse(self.responseText, ["head", "body", "script"], 5000);
		}
		popup_msg.close();
		await tools.sleep(300);
		if (data) {
			popup_msg.createPopup(data["head"], data["body"]);
			if (data["script"]) {
				let script = document.createElement("script");
				script.innerHTML = data["script"];
				document.body.appendChild(script);
			}
		} else {
			popup_msg.createPopup("Failed", "Server didn't respond<br>response: " + self.status);
		}
		popup_msg.open_popup();
	}
	menu_click(action, link, more_data = null, callback = null) {
		let that = this;
		popup_msg.close();

		let url = ".?" + action;
		let xhr = new XMLHttpRequest();
		xhr.open("POST", url);
		xhr.onreadystatechange = function () {
			if (this.readyState === 4) {
				that.on_result(this);
				if (callback) {
					callback();
				}
			}
		};
		const formData = new FormData();
		formData.append("post-type", action);
		formData.append("name", link);
		formData.append("data", more_data);
		xhr.send(formData);
	}
	rename_data() {
		let new_name = byId("input_rename").value;

		this.menu_click("rename", this.old_name, new_name, null, () => { page_controller.refresh_dir() });
		// popup_msg.createPopup("Done!", "New name: "+new_name)
		// popup_msg.open_popup()
	}
	async rename(link, name) {
		await popup_msg.close();
		popup_msg.createPopup("Rename",
			"Enter new name: <input id='input_rename' type='text'><br><br><div class='pagination center' onclick='context_menu.rename_data()'>Change!</div>"
		);
		
		popup_msg.open_popup();
		this.old_name = link;
		byId("input_rename").value = name;
		byId("input_rename").focus();
	}
	show_menus(file, name, type) {
		let that = this;
		let menu = createElement("div");


		const refresh = () => {
			page_controller.refresh_dir();
		}

		let new_tab = createElement("div");
		new_tab.innerText = "↗️" + " New tab";
		new_tab.className = "disable_selection popup-btn menu_options";
		new_tab.onclick = function () {
			window.open(file, '_blank');
			popup_msg.close();
		}
		menu.appendChild(new_tab);
		if (type != "folder") {
			let download = createElement("div");
			download.innerText = "📥" + " Download";
			download.className = "disable_selection popup-btn menu_options";
			download.onclick = function () {
				tools.download(file, name);
				popup_msg.close();
			}
			if (user.permissions.DOWNLOAD) {
				menu.appendChild(download);
			}
		}
		if (type == "folder") {
			let dl_zip = createElement("div");
			dl_zip.innerText = "📦" + " Download as Zip";
			dl_zip.className = "disable_selection popup-btn menu_options";
			dl_zip.onclick = function () {
				popup_msg.close();
				window.open(go_link('czip', file), '_blank');
				// czip = "Create Zip"
			}
			if (user.permissions.ZIP) {
				menu.appendChild(dl_zip);
			}
		}

		let copy = createElement("div");
		copy.innerText = "📋" + " Copy link";
		copy.className = "disable_selection popup-btn menu_options";
		copy.onclick = async function (ev) {
			popup_msg.close();

			let success = await tools.copy_2(ev, tools.full_path(file));
			if (success) {
				toaster.toast("Link Copied!");
			} else {
				toaster.toast("Failed to copy!");
			}
		}
		menu.appendChild(copy);

		let rename = createElement("div");
		rename.innerText = "✏️" + " Rename";
		rename.className = "disable_selection popup-btn menu_options";
		rename.onclick = function () {
			that.rename(file, name);
		}

		if (user.permissions.MODIFY) {
			menu.appendChild(rename);
		}

		let del = createElement("div");
		del.innerText = "🗑️" + " Delete";
		del.className = "disable_selection popup-btn menu_options";
		var xxx = 'F';
		if (type == "folder") {
			xxx = 'D';
		}
		del.onclick = function () {
			that.menu_click('del-f', file, null, refresh);
		};

		if (user.permissions.DELETE) {
			menu.appendChild(del);
		}

		let del_P = createElement("div");
		del_P.innerText = "🔥" + " Delete permanently";
		del_P.className = "disable_selection popup-btn menu_options";


		del_P.onclick = () => {
			r_u_sure({
				y: () => {
					that.menu_click('del-p', file, null, refresh);
				}, head: "Are you sure?", body: "This can't be undone!!!", y_msg: "Continue", n_msg: "Cancel"
			})
		}

		if (user.permissions.DELETE) {
			menu.appendChild(del_P);
		}

		let property = createElement("div");
		property.innerText = "📅" + " Properties";
		property.className = "disable_selection popup-btn menu_options";
		property.onclick = function () {
			that.menu_click('info', file);
		};

		if (user.permissions.VIEW) {
			menu.appendChild(property);
		}

		popup_msg.createPopup("Menu", menu);
		popup_msg.open_popup();
	}
	create_folder() {
		let folder_name = byId('folder-name').value;
		this.menu_click('new_folder', folder_name, null, () => { page_controller.refresh_dir() });
	}
}
var context_menu = new ContextMenu();
//context_menu.show_menus("next", "video");

function show_response(url, add_reload_btn = true) {
	let xhr = new XMLHttpRequest();
	xhr.onreadystatechange = function () {
		if (xhr.readyState == XMLHttpRequest.DONE) {
			let msg = xhr.responseText;
			if (add_reload_btn) {
				msg = msg + "<br><br><div class='pagination' onclick='window.location.reload()'>Refresh🔄️</div>";
			}
			popup_msg.close();
			popup_msg.createPopup("Result", msg);
			popup_msg.open_popup();
		}
	}
	xhr.open('GET', url, true);
	xhr.send(null);
}

function reload() {
	show_response("/?reload");
}


function insertAfter(newNode, existingNode) {
	existingNode.parentNode.insertBefore(newNode, existingNode.nextSibling);
}

function fmbytes(B) {
	'Return the given bytes as a file manager friendly KB, MB, GB, or TB string'
	let KB = 1024,
		MB = (KB ** 2),
		GB = (KB ** 3),
		TB = (KB ** 4)

	var unit = "byte", val = B;

	if (B > 1) {
		unit = "bytes";
		val = B;
	}
	if (B / KB > 1) {
		val = (B / KB);
		unit = "KB";
	}
	if (B / MB > 1) {
		val = (B / MB);
		unit = "MB";
	}
	if (B / GB > 1) {
		val = (B / GB);
		unit = "GB";
	}
	if (B / TB > 1) {
		val = (B / TB);
		unit = "TB";
	}

	val = val.toFixed(2);

	return `${val} ${unit}`;
}




class ProgressBars {
	constructor() {
		this.bars = {};
		/* Data Structure
		{index: {
			type: "upload", or "zip"
			status: "waiting" | "running" | "done" | "error"
			form_id: 0, // UploadManager.uploaders[form_id]
			persent: 0,
			source_dir: "", // location from where the file is being uploaded
			status_text: "", // status text
			status_color: "", // status color for the text
		}, ...} */
		this.bar_elements = {};

		this.island_bar = byId("progress-island");
		this.island_up_text = byId("progress-uploads");
		this.island_up_count = byId("progress-uploads-count");

		this.island_zip_text = byId("progress-zips");
		this.island_zip_count = byId("progress-zips-count");
	}

	new(type, id, source_dir, callbacks = {}) {
		let index = id;

		let bar = {
			type: type,
			form_id: id,
			percent: 0,
			source_dir: source_dir,
			status_text: "",
			status_color: "",
		}
		this.bars[index] = bar;
		this.bar_elements[index] = null; // will be set later


		let bar_element = createElement("div");
		bar_element.className = "progress_bar";
		bar_element.id = "progress_bar_" + index;

		let bar_head = createElement("div");
		bar_head.className = "progress_bar_heading";

		let bar_head_text = createElement("div");
		bar_head_text.className = "progress_bar_heading_text";
		if (type == "upload") {
			bar_head_text.innerText = "Uploading";
		} else if (type == "zip") {
			bar_head_text.innerText = "Zipping";
		}
		bar_head_text.style.float = "left";
		bar_head.appendChild(bar_head_text);

		let bar_status = createElement("div");
		bar_status.className = "progress_bar_status";
		bar_status.innerText = "0%";
		bar_status.style.float = "right";
		bar_head.appendChild(bar_status);
		bar_element.appendChild(bar_head);


		let status_label = createElement("span");
		status_label.style.font_size = ".6em";
		status_label.innerText = "Status: ";
		bar_element.appendChild(status_label);

		let bar_status_text = createElement("span");
		bar_status_text.className = "progress_bar_status_text";
		bar_status_text.innerText = "Waiting";
		bar_element.appendChild(bar_status_text);

		let bar_progress = createElement("progress");
		bar_progress.className = "progress_bar_progress";
		bar_progress.value = 0;
		bar_progress.max = 100;
		bar_element.appendChild(bar_progress);

		bar_element.appendChild(createElement("br"));

		let bar_cancel = createElement("span");
		bar_cancel.className = "progress_bar_cancel";
		bar_cancel.innerHTML = "&#9888; Delete Task";
		bar_cancel.onclick = function (e) {
			e.stopPropagation(); // stop the click event from propagating to the bar element
			callbacks.oncancel && callbacks.oncancel();
		}
		bar_element.appendChild(bar_cancel);

		bar_element.onclick = () => {
			callbacks.onclick && callbacks.onclick();
		}


		this.bar_elements[index] = bar_element;

		return index;

	}


	update_island() {
		let up_count = 0;
		let up_done_count = 0;
		let zip_count = 0;
		let zip_done_count = 0;
		for (let index in this.bars) {
			let bar = this.bars[index];
			if (bar.type == "upload") {
				up_count += 1;
				if (bar.status == "done") {
					up_done_count += 1;
				}
			} else if (bar.type == "zip") {
				zip_count += 1;
				if (bar.status == "done") {
					zip_done_count += 1;
				}
			}
		}

		this.island_bar.style.display = "block";
		if (!(up_count || zip_count)) {
			this.island_bar.style.display = "None";
			return;
		}


		if (up_count) {
			this.island_up_text.style.display = "block";
			this.island_up_count.innerText = "(" + up_done_count + '/' + up_count + ')';
		} else {
			this.island_up_text.style.display = "none";
		}

		if (zip_count) {
			this.island_zip_text.style.display = "block";
			this.island_zip_count.innerText = "(" + zip_done_count + '/' + zip_count + ')';
		} else {
			this.island_zip_text.style.display = "none";
		}
	}


	update(index, datas = {}) {
		let bar = this.bars[index];
		for (let key in datas) {
			bar[key] = datas[key];
		}
		this.update_bar(index);
	}

	update_bar(index) {
		let bar = this.bars[index];
		let bar_element = this.bar_elements[index];
		let type = bar.type;



		let bar_head_text = bar_element.getElementsByClassName("progress_bar_heading_text")[0];
		if (type == "upload") {
			bar_head_text.innerText = "Uploading";
		} else if (type == "zip") {
			bar_head_text.innerText = "Zipping";
		}

		let bar_status = bar_element.getElementsByClassName("progress_bar_status")[0];
		bar_status.className = "progress_bar_status";
		bar_status.innerText = bar.percent + "%"

		let bar_status_text = bar_element.getElementsByClassName("progress_bar_status_text")[0];
		bar_status_text.innerText = bar.status_text || "Waiting";
		bar_status_text.style.color = bar.status_color || "white";



		let bar_progress = bar_element.getElementsByClassName("progress_bar_progress")[0];
		bar_progress.value = bar.percent;

		this.update_island();
	}

	show_list() {
		let list = createElement("div");
		list.className = "progress_bar_list";

		let heading = createElement("h3");
		heading.innerText = "Do not close this tab while tasks are running";
		list.appendChild(heading);
		list.appendChild(createElement("hr"));


		for (let index in this.bars) {
			let bar = this.bars[index];
			let bar_element = this.bar_elements[index];
			list.appendChild(bar_element);
		}

		popup_msg.createPopup("Running Tasks", list);

		popup_msg.open_popup();
	}

	remove(index) {
		// check if the index exists
		if (!(index in this.bars)) {
			return; // to avoid recursion
		}

		delete this.bars[index] // remove the id 1st
		let bar_element = this.bar_elements[index];
		bar_element.remove(); // remove the element from the DOM
		delete this.bar_elements[index]; // remove the element from the list

		toaster.toast("Task removed");
		this.update_island();
	}
}

const progress_bars = new ProgressBars();
progress_bars.update_island();














class User {
	constructor() {
		this.user = null;
		this.token = null;
		this.permissions_code = null;
		this.permissions = null;

		this.all_permissions = [
			'VIEW',
			'DOWNLOAD',
			'MODIFY',
			'DELETE',
			'UPLOAD',
			'ZIP',
			'ADMIN',
			'MEMBER',
		];
	}

	get_user() {
		this.user = tools.getCookie("user");
		this.token = tools.getCookie("token");
		this.permissions_code = tools.getCookie("permissions") || 0;

		this.permissions = {
			// NOPERMISSIONS: false is not needed since its handled by the server
			'VIEW': false,
			'DOWNLOAD': false,
			'MODIFY': false,
			'DELETE': false,
			'UPLOAD': false,
			'ZIP': false,
			'ADMIN': false,
			'MEMBER': false,
		};
		this.extract_permissions();
	}

	extract_permissions() {
		// this function extracts the permissions from the permissions_code
		let permissions = this.all_permissions;
		this.permissions = {}
		permissions.forEach((permission, i) => {
			this.permissions[permission] = this.permissions_code >> i & 1;
		}, this);
		// if none of permission is true, add nopermission to the permissions
		if (!Object.values(this.permissions).some(x => !!x)) {
			this.permissions['NOPERMISSION'] = true;
		} else {
			this.permissions['NOPERMISSION'] = false;
		}

		return this.permissions;


	}

	pack_permissions() {
		// this function packs the permissions into permissions_code
		let permissions = this.all_permissions;

		this.permissions_code = 0;
		permissions.forEach((permission, i) => {
			this.permissions_code |= this.permissions[permission] << i;
		}, this);

		return this.permissions_code;
	}

}

const user = new User();
user.get_user();




// /////////////////////////////
//    Show Admin Only Stuffs  //
// /////////////////////////////

{
	if (user.permissions.ADMIN) {
		let css = document.createElement("style");
		css.innerHTML = `
		.admin_only {
			display: block;
		}
		`;
		document.body.appendChild(css);
	}

	if (user.permissions.MEMBER) {
		let css = document.createElement("style");
		css.innerHTML = `
		.member_only {
			display: block;
		}
		`;
		document.body.appendChild(css);
	} else {
		let css = document.createElement("style");
		css.innerHTML = `
		.guest_only {
			display: none;
		}
		`;
		document.body.appendChild(css);
	}

	if (config.allow_Debugging) {
		let css = document.createElement("style");
		css.innerHTML = `
		.debug_only {
			display: block;
		}
		`;
		document.body.appendChild(css);
	}
}
