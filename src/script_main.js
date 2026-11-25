


class ContextMenu {
	constructor() {
		this.old_name = null;
	}
	async on_result(self) {
		var data = false;
		if (self.status == 200) {
			data = tools.safeJSONParse(self.responseText, ["status", "head", "body", "script"], 5000);
		}
		popup_msg.close();
		await tools.sleep(300);
		if (data) {
			const isSuccess = data.status === true;
			const head = data.head || (isSuccess ? "Success" : "Failed");
			const headIcon = isSuccess
				? "<span class='fa fa-solid fa-circle-check' style='color:var(--color-success);margin-right:8px;'>✅</span> "
				: "<span class='fa fa-solid fa-circle-xmark' style='color:var(--color-danger);margin-right:8px;'>❌</span> ";
			
			let bodyContent = data.body || "";
			if (isSuccess) {
				page_controller.refresh_dir();
			}

			if (head !== "Properties") {
				bodyContent += "<div class='popup-actions-row' style='justify-content:center;margin-top:16px;'><button type='button' class='btn btn-primary' onclick='popup_msg.close()'>OK</button></div>";
			}

			popup_msg.createPopup(headIcon + head, bodyContent);
			if (data.script) {
				let script = document.createElement("script");
				script.innerHTML = data.script;
				document.body.appendChild(script);
			}
		} else {
			popup_msg.createPopup(
				"<span class='fa fa-solid fa-circle-xmark' style='color:var(--color-danger);margin-right:8px;'>❌</span> Failed",
				"<div class='popup-dialog-msg'>Server didn't respond<br>Status: " + self.status + "</div><div class='popup-actions-row' style='justify-content:center;'><button type='button' class='btn' onclick='popup_msg.close()'>OK</button></div>"
			);
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

		this.menu_click("rename", this.old_name, new_name);
	}
	async rename(link, name) {
		await popup_msg.close();
		popup_msg.createPopup("Rename",
			`<div class="popup-form">
				<label class="popup-form-label">Enter new name:</label>
				<input id="input_rename" class="popup-input" type="text" autocomplete="off" spellcheck="false">
				<div class="popup-actions-row">
					<button type="button" class="btn btn-primary" onclick="context_menu.rename_data()">Change</button>
					<button type="button" class="btn" onclick="popup_msg.close()">Cancel</button>
				</div>
			</div>`
		);
		
		popup_msg.open_popup();
		this.old_name = link;
		const input = byId("input_rename");
		if (input) {
			input.value = name;
			input.focus();
			input.select();
			input.onkeydown = (e) => {
				if (e.key === "Enter") {
					this.rename_data();
				}
			};
		}
	}
	create_menu_item(emoji, faClass, text, onClick, extraClass = "") {
		let item = createElement("div");
		item.className = "disable_selection popup-btn menu_options" + (extraClass ? " " + extraClass : "");

		let iconSpan = createElement("span");
		iconSpan.className = "menu-icon fa " + faClass;
		iconSpan.innerText = emoji;

		let labelSpan = createElement("span");
		labelSpan.className = "menu-label";
		labelSpan.innerText = text;

		item.appendChild(iconSpan);
		item.appendChild(labelSpan);

		if (theme_controller.fa_ok) {
			theme_controller.del_fa_alt(iconSpan);
		}

		item.onclick = onClick;
		return item;
	}

	show_menus(file, name, type) {
		let that = this;
		let menu = createElement("div");

		let new_tab = that.create_menu_item("↗️", "fa-solid fa-arrow-up-right-from-square", "New tab", function () {
			window.open(file, '_blank');
			popup_msg.close();
		});
		menu.appendChild(new_tab);
		
		// Add "Open in Editor" option for text files
		if (type != "folder") {
			const text_extensions = ['.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.htm', '.css', '.scss', '.less', 
									  '.json', '.xml', '.md', '.txt', '.sql', '.java', '.cpp', '.c', '.h', '.go', 
									  '.rs', '.php', '.rb', '.yaml', '.yml', '.sh', '.bash', '.conf', '.cfg', '.ini', 
									  '.properties', '.gradle', '.maven'];
			const file_ext = name.substr(name.lastIndexOf('.')).toLowerCase();
			
			if (text_extensions.includes(file_ext)) {
				let open_editor = that.create_menu_item("✎", "fa-solid fa-pen-to-square", "Open in Editor", function () {
					popup_msg.close();
					// Navigate to editor view
					window.location.href = go_link('edit', file);
				});
				menu.appendChild(open_editor);
			}
		}
		
		if (type != "folder") {
			let download = that.create_menu_item("📥", "fa-solid fa-download", "Download", function () {
				tools.download(file, name);
				popup_msg.close();
			});
			if (user.permissions.DOWNLOAD) {
				menu.appendChild(download);
			}
		}
		if (type == "folder") {
			let dl_zip = that.create_menu_item("📦", "fa-solid fa-file-zipper", "Download as Zip", function () {
				popup_msg.close();
				window.open(go_link('czip', file), '_blank');
				// czip = "Create Zip"
			});
			if (user.permissions.ZIP) {
				menu.appendChild(dl_zip);
			}
		}

		let copy = that.create_menu_item("📋", "fa-solid fa-copy", "Copy link", async function (ev) {
			popup_msg.close();

			let success = await tools.copy_2(ev, tools.full_path(file));
			if (success) {
				toaster.toast("Link Copied!");
			} else {
				toaster.toast("Failed to copy!");
			}
		});
		menu.appendChild(copy);

		let rename = that.create_menu_item("✏️", "fa-solid fa-pen", "Rename", function () {
			that.rename(file, name);
		});

		if (user.permissions.MODIFY) {
			menu.appendChild(rename);
		}

		let del = that.create_menu_item("🗑️", "fa-solid fa-trash-can", "Delete", function () {
			that.menu_click('del-f', file);
		}, "menu_options_danger");

		if (user.permissions.DELETE) {
			menu.appendChild(del);
		}

		let del_P = that.create_menu_item("🔥", "fa-solid fa-fire", "Delete permanently", () => {
			r_u_sure({
				y: () => {
					that.menu_click('del-p', file);
				}, head: "Are you sure?", body: "This can't be undone!!!", y_msg: "Continue", n_msg: "Cancel"
			})
		}, "menu_options_danger");

		if (user.permissions.DELETE) {
			menu.appendChild(del_P);
		}

		let property = that.create_menu_item("📅", "fa-solid fa-circle-info", "Properties", function () {
			that.menu_click('info', file);
		});

		if (user.permissions.VIEW) {
			menu.appendChild(property);
		}

		popup_msg.createPopup("Menu", menu);
		popup_msg.open_popup();
	}
	create_folder() {
		let folder_name = byId('folder-name').value;
		this.menu_click('new_folder', folder_name);
	}
}
var context_menu = new ContextMenu();
//context_menu.show_menus("next", "video");

function show_response(url) {
	let xhr = new XMLHttpRequest();
	xhr.onreadystatechange = function () {
		if (xhr.readyState == XMLHttpRequest.DONE) {
			let msg = xhr.responseText;
			page_controller.refresh_dir();
			popup_msg.close();
			popup_msg.createPopup(
				"Result",
				msg + "<div class='popup-actions-row' style='justify-content:center;margin-top:16px;'><button type='button' class='btn btn-primary' onclick='popup_msg.close()'>OK</button></div>"
			);
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
