



class ContextMenu {
	constructor() {
		this.old_name = null;
	}
	async on_result(self) {
		var data = false;
		if (self.status == 200) {
			data = safeJSONParse(self.responseText, ["head", "body", "script"], 5000);
		}
		popup_msg.close()
		await tools.sleep(300)
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
		popup_msg.open_popup()
	}
	menu_click(action, link, more_data = null) {
		let that = this
		popup_msg.close()

		let url = ".?"+action;
		let xhr = new XMLHttpRequest();
		xhr.open("POST", url);
		xhr.onreadystatechange = function() {
			if (this.readyState === 4) {
				that.on_result(this)
			}
		};
		const formData = new FormData();
		formData.append("post-type", action);
		formData.append("post-uid", 123456); // TODO: add uid
		formData.append("name", link);
		formData.append("data", more_data)
		xhr.send(formData);
	}
	rename_data() {
		let new_name = byId("rename").value;

		this.menu_click("rename", this.old_name, new_name)
		// popup_msg.createPopup("Done!", "New name: "+new_name)
		// popup_msg.open_popup()
	}
	rename(link, name) {
		popup_msg.close()
		popup_msg.createPopup("Rename",
			"Enter new name: <input id='rename' type='text'><br><br><div class='pagination center' onclick='context_menu.rename_data()'>Change!</div>"
			);
		popup_msg.open_popup()
		this.old_name = link;
		byId("rename").value = name;
		byId("rename").focus()
	}
	show_menus(file, name, type) {
		let that = this;
		let menu = createElement("div")

		let new_tab = createElement("div")
			new_tab.innerText = "↗️" + " New tab"
			new_tab.className = "disable_selection popup-btn menu_options"
			new_tab.onclick = function() {
				window.open(file, '_blank');
				popup_msg.close()
			}
			menu.appendChild(new_tab)
		if (type != "folder") {
			let download = createElement("div")
			download.innerText = "📥" + " Download"
			download.className = "disable_selection popup-btn menu_options"
			download.onclick = function() {
				tools.download(file, name);
				popup_msg.close()
			}
			if(user.permissions.DOWNLOAD){
				menu.appendChild(download)
			}
		}
		if (type == "folder") {
			let dl_zip = createElement("div")
			dl_zip.innerText = "📦" + " Download as Zip"
			dl_zip.className = "disable_selection popup-btn menu_options"
			dl_zip.onclick = function() {
				popup_msg.close()
				window.open(go_link('czip', file), '_blank');
				// czip = "Create Zip"
			}
			if(user.permissions.ZIP){
				menu.appendChild(dl_zip)
			}
		}

		let copy = createElement("div")
		copy.innerText = "📋" + " Copy link"
		copy.className = "disable_selection popup-btn menu_options"
		copy.onclick = async function(ev) {
			popup_msg.close()

			let success = await tools.copy_2(ev, tools.full_path(file))
			if(success){
				toaster.toast("Link Copied!")
			}else{
				toaster.toast("Failed to copy!")
			}
		}
		menu.appendChild(copy)

		let rename = createElement("div")
		rename.innerText = "✏️" + " Rename"
		rename.className = "disable_selection popup-btn menu_options"
		rename.onclick = function() {
			that.rename(file, name)
		}

		if (user.permissions.RENAME) {
			menu.appendChild(rename)
		}
		
		let del = createElement("div")
		del.innerText = "🗑️" + " Delete"
		del.className = "disable_selection popup-btn menu_options"
		var xxx = 'F'
		if (type == "folder") {
			xxx = 'D'
		}
		del.onclick = function() {
			that.menu_click('del-f', file);
		};
		
		if (user.permissions.DELETE) {
			menu.appendChild(del)
		}

		let del_P = createElement("div")
		del_P.innerText = "🔥" + " Delete permanently"
		del_P.className = "disable_selection popup-btn menu_options"


		del_P.onclick = () => {
			r_u_sure({y:()=>{
				that.menu_click('del-p', file);
			}, head:"Are you sure?", body:"This can't be undone!!!", y_msg:"Continue", n_msg:"Cancel"})
		}

		if (user.permissions.DELETE) {
			menu.appendChild(del_P)
		}

		let property = createElement("div")
		property.innerText = "📅" + " Properties"
		property.className = "disable_selection popup-btn menu_options"
		property.onclick = function() {
			that.menu_click('info', file);
		};

		if (user.permissions.READ) {
			menu.appendChild(property)
		}
		
		popup_msg.createPopup("Menu", menu)
		popup_msg.open_popup()
	}
	create_folder() {
		let folder_name = byId('folder-name').value;
		this.menu_click('new_folder', folder_name)
	}
}
var context_menu = new ContextMenu()
//context_menu.show_menus("next", "video")

function show_response(url, add_reload_btn = true) {
	let xhr = new XMLHttpRequest();
	xhr.onreadystatechange = function() {
		if (xhr.readyState == XMLHttpRequest.DONE) {
			let msg = xhr.responseText;
			if (add_reload_btn) {
				msg = msg + "<br><br><div class='pagination' onclick='window.location.reload()'>Refresh🔄️</div>";
			}
			popup_msg.close()
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

	var unit="byte", val=B;

	if (B>1){
		unit="bytes"
		val = B}
	if (B/KB>1){
		val = (B/KB)
		unit="KB"}
	if (B/MB>1){
		val = (B/MB)
		unit="MB"}
	if (B/GB>1){
		val = (B/GB)
		unit="GB"}
	if (B/TB>1){
		val = (B/TB)
		unit="TB"}

	val = val.toFixed(2)

	return `${val} ${unit}`
}




class ProgressBars {
	constructor() {
		this.last_index = 1
		this.bars = {}
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
		this.bar_elements = {}

		this.island_bar = byId("progress-island")
		this.island_up_text = byId("progress-uploads")
		this.island_up_count = byId("progress-uploads-count")
		
		this.island_zip_text = byId("progress-zips")
		this.island_zip_count = byId("progress-zips-count")
	}

	new(type, id, source_dir) {
		let that = this;
		let index = this.last_index;
		this.last_index += 1;

		let bar = {
			type: type,
			form_id: id,
			percent: 0,
			source_dir: source_dir,
			status_text: "",
			status_color: "",
		}
		this.bars[index] = bar
		this.bar_elements[index] = null // will be set later


		let bar_element = createElement("div")
		bar_element.className = "progress_bar"
		bar_element.id = "progress_bar_" + index

		let bar_head = createElement("div")
		bar_head.className = "progress_bar_heading"
		
		let bar_head_text = createElement("div")
		bar_head_text.className ="progress_bar_heading_text"
		if(type=="upload"){
			bar_head_text.innerText = "Uploading"
		} else if(type=="zip"){
			bar_head_text.innerText = "Zipping"
		}
		bar_head_text.style.float ="left"
		bar_head.appendChild(bar_head_text)

		let bar_status = createElement("div")
		bar_status.className = "progress_bar_status"
		bar_status.innerText = "0%"
		bar_status.style.float = "right" 
		bar_head.appendChild(bar_status)
		bar_element.appendChild(bar_head)
		
		
		let status_label = createElement("span")
		status_label.style.font_size = ".6em"
		status_label.innerText = "Status: "
		bar_element.appendChild(status_label)

		let bar_status_text = createElement("span")
		bar_status_text.className = "progress_bar_status_text"
		bar_status_text.innerText = "Waiting"
		bar_element.appendChild(bar_status_text)

		let bar_progress = createElement("progress")
		bar_progress.className = "progress_bar_progress"
		bar_progress.value = 0
		bar_progress.max = 100
		bar_element.appendChild(bar_progress)

		bar_element.appendChild(createElement("br"))

		let bar_cancel = createElement("span")
		bar_cancel.className = "progress_bar_cancel"
		bar_cancel.innerHTML = "&#9888; Delete Task"
		bar_cancel.onclick = function(e){
			e.stopPropagation() // stop the click event from propagating to the bar element
			if (type == "upload") {
				upload_man.remove(id)
			} else if (type == "zip") {
				zip_man.cancel(id)
			}

			that.remove(index)
		}
		bar_element.appendChild(bar_cancel)

		bar_element.onclick = ()=>{
			if(type=="upload") {
				upload_man.show(id)
			} else if(type=="zip") {
				zip_man.show(id)
			}
		}


		this.bar_elements[index] = bar_element

		return index

	}

	
	update_island() {
		let up_count = 0
		let up_done_count = 0
		let zip_count = 0
		let zip_done_count = 0
		for (let index in this.bars) {
			let bar = this.bars[index]
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
		
		this.island_bar.style.display = "block"
		if (!(up_count||zip_count)){
			this.island_bar.style.display = "None"
			return
		}

		
		if (up_count){
			this.island_up_text.style.display = "block"
			this.island_up_count.innerText = "(" + up_done_count + '/' + up_count + ')'
		} else {
			this.island_up_text.style.display = "none"
		}
		
		if (zip_count){
			this.island_zip_text.style.display = "block"
			this.island_zip_count.innerText = "(" + zip_done_count + '/' + zip_count + ')'
		} else {
			this.island_zip_text.style.display = "none"
		} 
	}


	update(index, datas={}) {
		let bar = this.bars[index]
		for (let key in datas) {
			bar[key] = datas[key]
		}
		this.update_bar(index)
	}

	update_bar(index){
		let bar = this.bars[index]
		let bar_element = this.bar_elements[index]
		let type = bar.type
		
		

		let bar_head_text = bar_element.getElementsByClassName("progress_bar_heading_text")[0]
		if(type=="upload"){
			bar_head_text.innerText = "Uploading"
		} else if(type=="zip"){
			bar_head_text.innerText = "Zipping"
		}

		let bar_status = bar_element.getElementsByClassName("progress_bar_status")[0]
		bar_status.className = "progress_bar_status"
		bar_status.innerText = bar.percent + "%"

		let bar_status_text = bar_element.getElementsByClassName("progress_bar_status_text")[0]
		bar_status_text.innerText = bar.status_text || "Waiting"
		bar_status_text.style.color = bar.status_color || "white"
		
		
		
		let bar_progress = bar_element.getElementsByClassName("progress_bar_progress")[0]
		bar_progress.value = bar.percent
		
		this.update_island()
	}

	show_list() {
		let list = createElement("div")
		list.className = "progress_bar_list"

		let heading = createElement("h3")
		heading.innerText = "Do not close this tab while tasks are running"
		list.appendChild(heading)
		list.appendChild(createElement("hr"))


		for (let index in this.bars) {
			let bar = this.bars[index]
			let bar_element = this.bar_elements[index]
			list.appendChild(bar_element)
		}
		
		popup_msg.createPopup("Running Tasks", list)

		popup_msg.open_popup()
	}

	remove(index) {
		// check if the index exists
		if (!(index in this.bars)) {
			return // to avoid recursion
		}

		delete this.bars[index] // remove the id 1st
		let bar_element = this.bar_elements[index]
		bar_element.remove() // remove the element from the DOM
		delete this.bar_elements[index] // remove the element from the list

		toaster.toast("Task removed")
		this.update_island()
	}
}

const progress_bars = new ProgressBars()
progress_bars.update_island()

















class User {
	constructor(){
		this.user = tools.getCookie("user") || "Guest";
		this.token = tools.getCookie("token") || "";
		this.permissions_code = tools.getCookie("permissions") || 0;

		this.permissions = {
			// NOPERMISSIONS: false is not needed since its handled by the server
			'READ': false,
			'DOWNLOAD': false,
			'MODIFY': false,
			'DELETE': false,
			'UPLOAD': false,
			'ZIP': false,
			'ADMIN': false,
		};
		this.extract_permissions();
	}

	extract_permissions(){
		// this function extracts the permissions from the permissions_code
		let permissions = [
			'READ',
			'DOWNLOAD',
			'MODIFY',
			'DELETE',
			'UPLOAD',
			'ZIP',
			'ADMIN',
		]
		permissions.forEach((permission, i) => {
			this.permissions[permission] = this.permissions_code >> i & 1;
		}, this);
		// if none of permission is true, add nopermission to the permissions
		if(!Object.values(this.permissions).includes(true)){
			this.permissions['NOPERMISSION'] = true;
		} else {
			this.permissions['NOPERMISSION'] = false;
		}


	}

}

const user = new User();
