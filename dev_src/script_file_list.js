var r_li = [] // ${PY_LINK_LIST};
var f_li = [] // ${PY_FILE_LIST};
var s_li = [] // ${PY_FILE_SIZE};


function clear_file_list() {
	// clear previous data
	tools.del_child("linkss");
	tools.del_child("js-content_list")
}


class FM_Page{
	constructor(){
		this.type = "dir"

		this.my_part = document.getElementById("fm_page")

	}

	on_action_button(){
		// show add folder, sort, etc
		fm.show_more_menu()
	}

	async initialize(lazyload=false){
		if (!lazyload){
			page.clear();
		}

		page.set_title("File Manager")
		page.set_actions_button_text("New&nbsp;")
		page.show_actions_button()

		if (user.permissions.NOPERMISSION || !user.permissions.VIEW){
			page.set_title("No Permission")

			const container = byId("js-content_list")
			const warning = createElement("h2")
			warning.innerText = "You don't have permission to view this page"
			container.appendChild(warning)

			return
		}

		var folder_data = await fetch(tools.add_query_here("folder_data"))
								.then(response => response.json())
								.catch(error => {
									console.error('There has been a problem with your fetch operation:', error); // TODO: Show error in page
								});

		if (!folder_data || !folder_data["status"] || folder_data.status == "error"){
			console.error("Error getting folder data") // TODO: Show error in page
			return
		}

		r_li = folder_data.type_list
		f_li = folder_data.file_list
		s_li = folder_data.size_list

		var title = folder_data.title

		page.set_title(title)


		show_file_list();
	}

	hide(){
		this.my_part.classList.remove("active");
	}

	show(){
		this.my_part.classList.add("active");
	}

	clear(){
		tools.del_child("linkss");
	}

}

const fm_page = new FM_Page();


class UploadManager {
	constructor() {
		let that = this;
		this.last_index = 1
		this.uploaders = {}
		this.requests = {}
		this.status = {}
		/* Data Structure
		{index: form_element, ...}
		*/

		var form = null;
		let file_list = byId("content_container")
		this.drag_pop_open = false;

		file_list.ondragover = async (event)=>{
			event.preventDefault(); //preventing from default behaviour
			if(that.drag_pop_open){
				return;
			}
			that.drag_pop_open = true;

			form = await upload_man.new()
			popup_msg.createPopup("Upload Files", form, true, onclose=()=>{
				that.drag_pop_open = false;
			})
			popup_msg.open_popup();

		};

			//If user leave dragged File from DropArea
		file_list.ondragleave = (event)=>{
			event.preventDefault(); //preventing from default behavior
			// form.remove();
		};

			//If user drop File on DropArea
		file_list.ondrop = (event)=>{
			event.preventDefault(); //preventing from default behavior
		};
	}

	async new() {
		//selecting all required elements
		let that = this;
		let index = this.last_index;
		this.last_index += 1;

		let Form = createElement("form")
		Form.id = "uploader-" + index
		Form.className = "jsonly"
		Form.method = "post"
		Form.action = tools.full_path("?upload") // the upload url, to use later from different pages
		Form.enctype = "multipart/form-data"

		let center = createElement("center")
		// centering the form


		let post_type = createElement("input")
		post_type.type = "hidden";
		post_type.name = "post-type";
		post_type.value = "upload";
		center.appendChild(post_type)


		let pass_header = createElement("span")
		pass_header.className = "upload-pass";
		pass_header.innerText = "Password:  ";
		center.appendChild(pass_header)

		let pass_input = createElement("input")
		pass_input.type = "password";
		pass_input.name = "password";
		pass_input.placeholder = "Password";
		pass_input.label = "Password";
		pass_input.className = "upload-pass-box";
		center.appendChild(pass_input)


		let up_files = createElement("input")
		up_files.type = "file";
		up_files.name = "file";
		up_files.multiple = true
		up_files.hidden = true;
		up_files.onchange = (e)=>{
			// USING THE BROWSE BUTTON
			let f = e.target.files; // this.files = [file1, file2,...];
			addFiles(f);
		};
		center.appendChild(up_files)


		center.appendChild(createElement("br"))
		center.appendChild(createElement("br"))

		let uploader_box = createElement("div")
		uploader_box.className = "upload-box";

			let uploader_dragArea = createElement("div")
			uploader_dragArea.className = "drag-area";
			uploader_dragArea.id = "drag-area";

			let up_icon = createElement("div")
			up_icon.className = "drag-icon";
			up_icon.innerText = "⬆️";
			uploader_dragArea.appendChild(up_icon)

			let up_text = createElement("header")
			up_text.innerText = "Drag & Drop to Upload File";
			uploader_dragArea.appendChild(up_text)

			let or_text = createElement("span")
			or_text.innerText = "OR"
			uploader_dragArea.appendChild(or_text)

			let up_button = createElement("button")
			up_button.type = "button";
			up_button.innerText = "Browse File";
			up_button.className = "drag-browse";
			up_button.onclick = (e)=>{
				e.preventDefault();
				up_files.click(); //if user click on the button then the input also clicked
			}
			uploader_dragArea.appendChild(up_button)

			uploader_dragArea.ondragover = (event)=>{
				event.preventDefault(); //preventing from default behavior
				uploader_dragArea.classList.add("active");
				up_text.innerText = "Release to Upload File";
			};

			//If user leave dragged File from DropArea
			uploader_dragArea.ondragleave = ()=>{
				uploader_dragArea.classList.remove("active");
				up_text.innerText = "Drag & Drop to Upload File";
			};

			//If user drop File on DropArea
			uploader_dragArea.ondrop = (event)=>{
				event.preventDefault(); //preventing from default behavior
				//getting user select file and [0] this means if user select multiple files then we'll select only the first one
				uploader_dragArea.classList.remove("active");
				up_text.innerText = "Drag & Drop to Upload File";

				addFiles(event.dataTransfer.files);
				// uploader_showFiles(); //calling function
			};

		uploader_box.appendChild(uploader_dragArea)
		center.appendChild(uploader_box)


		Form.appendChild(center)

		let uploader_file_container = createElement("div")
		// uploader_file_container.style.display = "contents";
		uploader_file_container.style.display = "none";

		let uploader_file_display = createElement("div")
		uploader_file_display.className = "drag-file-list";

		let uploader_file_display_title = createElement("h2")
		uploader_file_display_title.innerText = "Selected Files"
		uploader_file_display_title.className = "has-selected-files";
		uploader_file_display_title.style.textAlign = "center";
		uploader_file_container.appendChild(uploader_file_display_title)
		uploader_file_container.appendChild(uploader_file_display)



		Form.appendChild(uploader_file_container)

		Form.appendChild(createElement("br"))
		let center2 = createElement("center")
		let submit_button = createElement("button")
		submit_button.type = "submit";
		submit_button.innerText = "➾ Upload";
		submit_button.className = "drag-browse upload-button";

		center2.appendChild(submit_button)

		center2.appendChild(createElement("br"))
		center2.appendChild(createElement("br"))

		let upload_pop_status_label = createElement("span")
		upload_pop_status_label.innerText = "Status: ";
		let upload_pop_status = createElement("span")
		upload_pop_status.className = "upload-pop-status";
		upload_pop_status.innerText = "Waiting";
		upload_pop_status_label.appendChild(upload_pop_status)
		upload_pop_status_label.style.display = "none";
		center2.appendChild(upload_pop_status_label)

		Form.appendChild(center2)

		let prog_id = null;
		let request = null;
		Form["prog_id"] = null; // This is used to update the progress bar

		Form.onsubmit = (e) => {
			e.preventDefault();

			if(that.status[index]){
				that.cancel(index);
				show_status("Upload cancelled");
				return;
			}

			if(selected_files.files.length == 0){
				toaster.toast("No files selected");
				return;
			}

			that.status[index] = true; // The user is uploading

			request = request || new XMLHttpRequest();
			that.requests[index] = request;
			that.uploaders[index] = Form; // Save the form for later use
			// Unless the user is uploading, this won't be saved


			submit_button.innerText = "⏹️ Cancel";

			popup_msg.close();

			up_files.files = selected_files.files; // Assign the updates list


			const formData = new FormData(e.target);

			prog_id = prog_id || progress_bars.new('upload', index, window.location.href); // Create a new progress bar if not already created
			Form.prog_id = prog_id; // Save the progress bar id for later use



			var prog = 0,
			msg = "",
			color = "green",
			upload_status = "waiting";


			progress_bars.update(prog_id, {
						"status_text": "Waiting",
						"status_color": color,
						"status": "waiting",
						"percent": 0});


			// const filenames = formData.getAll('files').map(v => v.name).join(', ')

			request.open(e.target.method, e.target.action);
			// request.timeout = 60 * 1000; // in case wifi have no internet, it will stop after 60 seconds
			request.onreadystatechange = () => {
				if (request.readyState === XMLHttpRequest.DONE) {
					msg = `${request.status}: ${request.statusText}`;
					upload_status = "error";
					color = "red";
					prog = 0;
					if (request.status === 401){
						msg = 'Incorrect password';
					} else if (request.status == 503) {
						msg = 'Upload is disabled';
					} else if (request.status === 0) {
						msg = 'Connection failed (Possible cause: Incorrect password or Upload disabled)';
					} else if (request.status === 204 || request.status === 200) {
						msg = 'Success';
						color = "green";
						prog = 100;
						upload_status = "done";

						page.refresh_dir(); // refresh the page if it is a dir page
					}


					progress_bars.update(prog_id, {
						"status_text": msg,
						"status_color": color,
						"status": upload_status,
						"percent": prog});

					submit_button.innerText = "➾ Re-upload";
					if (!that.status[index]){
						return; // needs to check this.status[index] because the user might have cancelled the upload but its still called. On cancel already a toast is shown
					}
					show_status(msg);

					if (upload_status === "error") {
						msg = "Upload Failed";
					} else {
						msg = "Upload Complete";
					}
					toaster.toast(msg, 3000, color);

					that.status[index] = false;

				}
			}
			request.upload.onprogress = e => {
				prog = Math.floor(100*e.loaded/e.total);
				if(e.loaded === e.total){
					msg ='Saving...';
					show_status(msg);
				}else{
					msg = `Progress`;
					show_status(msg + " " + prog + "%");
				}


				progress_bars.update(prog_id, {
						"status_text": msg,
						"status_color": "green",
						"status": "running",
						"percent": prog});
			}
			
			request.setRequestHeader('Cache-Control','no-cache');
			request.setRequestHeader("Connection", "close");
			request.send(formData);
		}


		let selected_files = new DataTransfer(); //this is a global variable and we'll use it inside multiple functions



		/**
		 * Displays a status message and optionally hides it.
		 * @param {string} msg - The message to display.
		 * @param {boolean} [hide=false] - Whether to hide the status message or not.
		 */
		function show_status(msg, hide=false){
			if(hide){
				upload_pop_status_label.style.display = "none";
				return;
			}
			upload_pop_status_label.style.display = "block";
			upload_pop_status.innerText = msg;
		}

		function truncate_file_name(name){
			// if bigger than 20, truncate, veryvery...last6chars
			if(name.length > 20){
				return name.slice(0, 7) + "..." + name.slice(-6);
			}
			return name;
		}

		function remove_duplicates(files) {
			for (let i = 0; i < files.length; i++) {
				var selected_fnames = [];
				const file = files[i];
				
				let exist = [...selected_files.files].findIndex(f => f.name === file.name);

				if (exist > -1) {
					// if file already selected,
					// remove that and replace with
					// new one, because, when uploading
					// last file will remain in host server,
					// so we need to replace it with new one
					toaster.toast(truncate_file_name(file.name) + " already selected", 1500);
					selected_files.items.remove(exist-1);
				}
				selected_files.items.add(file);
			};
		}


		/**
		 * Adds files to the selected files list and replaces any existing file with the same name.
		 * @param {FileList} files - The list of files to add.
		 */
		function addFiles(files) {

			remove_duplicates(files);
			

			log("selected "+ selected_files.items.length+ " files");
			uploader_showFiles();
		}

		function uploader_removeFileFromFileList(index) {
			let dt = new DataTransfer();
			// const input = byId('files')
			// const { files } = input

			for (let i = 0; i < selected_files.files.length; i++) {
				let file = selected_files.files[i]
				if (index !== i) {
					dt.items.add(file) // here you exclude the file. thus removing it.
				}
			}

			selected_files = dt
			// uploader_input.files = dt // Assign the updates list
			uploader_showFiles()
		}

		function uploader_showFiles() {
			tools.del_child(uploader_file_display)

			if(selected_files.files.length){
				uploader_file_container.style.display = "contents"
			} else {
				uploader_file_container.style.display = "none"
			}

			for (let i = 0; i <selected_files.files.length; i++) {
				uploader_showFile(selected_files.files[i], i);
			};
		}


		function uploader_showFile(file, index){
			let filename = file.name;
			let size = fmbytes(file.size);

			let item = createElement("table");
			item.className = "upload-file-item";

			let fname = createElement("td");
			fname.className = "ufname";
			fname.innerText = filename;
			item.appendChild(fname);

			let fsize = createElement("td");
			fsize.className = "ufsize";
			let fsize_text = createElement("span");
			fsize_text.innerText = size;
			fsize.appendChild(fsize_text);
			item.appendChild(fsize);

			let fremove = createElement("td");
			fremove.className = "ufremove";
			let fremove_icon = createElement("span");
			fremove_icon.innerHTML = "&times;";
			fremove_icon.onclick = function(){
				uploader_removeFileFromFileList(index)
			}
			fremove.appendChild(fremove_icon);
			item.appendChild(fremove);

			uploader_file_display.appendChild(item);

		}



		return Form;


	}

	up_stat(form, stat=null) {
		if(stat===null){
			return form.getAttribute("uploading");
		}
		form.setAttribute("uploading", stat);
	}

	show(index){
		let form = this.uploaders[index];
		popup_msg.createPopup("Upload Files", form);
		popup_msg.show();
	}

	cancel(index, remove=false){
		let request = this.requests[index];
		let form = this.uploaders[index];
		let prog_id = form.prog_id;

		if(form){
			form.querySelector(".upload-button").innerText = "➾ Upload";
		}
		progress_bars.update(prog_id, {
			"status_text": "Upload Canceled",
			"status_color": "red",
			"status": "error",
			"percent": 0})


		if(this.status[index]){
			this.status[index] = false;
			if(request){
				request.abort();
			}
			if(!remove) toaster.toast("Upload Canceled");

			return true;
		}

		return false;
	}

	remove(index){
		this.cancel(index, true); //cancel the upload (true to make sure it doesn't show toast)
		let form = this.uploaders[index];
		let prog_id = form.prog_id;
		if (prog_id){
			progress_bars.remove(prog_id);
		}
		this.uploaders[index].remove(); //remove the form from DOM
		delete this.uploaders[index]; //remove the form from uploaders array
		delete this.requests[index]; //remove the request from requests array
	}

}

const upload_man = new UploadManager();


class FileManager {
	constructor() {
	}

	show_more_menu(){
		let that = this;
		let menu = createElement("div")

		let sort_by = createElement("div")
		sort_by.innerText = "Sort By"
		sort_by.className = "disable_selection popup-btn menu_options debug_only"
		sort_by.onclick = function(){
			that.Show_sort_by()
		}
		menu.appendChild(sort_by)

		let new_folder = createElement("div")
		new_folder.innerText = "New Folder"
		new_folder.onclick = function(){
			that.Show_folder_maker()
		}
		new_folder.className = "disable_selection popup-btn menu_options"
		menu.appendChild(new_folder)

		let upload = createElement("div")
		upload.innerText = "Upload Files"
		upload.className = "disable_selection popup-btn menu_options"
		if (user.permissions.NOPERMISSION || !user.permissions.UPLOAD){
			upload.className += " disabled"
		} else {
			upload.onclick = function(){
				that.Show_upload_files()
			}
		}
		menu.appendChild(upload)

		popup_msg.createPopup("Options", menu)

		popup_msg.open_popup()
	}


	Show_folder_maker() {
		popup_msg.createPopup("Create Folder",
			"Enter folder name: <input id='folder-name' type='text'><br><br><div class='pagination center' onclick='context_menu.create_folder()'>Create</div>"
			);
		popup_msg.open_popup();
	}

	async Show_upload_files() {
		let form = await upload_man.new()
		popup_msg.createPopup("Upload Files", form);
		popup_msg.open_popup();
	}



}

const fm = new FileManager();





function show_file_list() {
	let folder_li = createElement('div');
	let file_li = createElement("div")
	r_li.forEach((r, i) => {
		// time to customize the links according to their formats
		var folder = false
		let type = null;
		// let r = r_li[i];
		let r_ = r.slice(1);
		let name = f_li[i];

		let item = createElement('div');
		item.classList.add("dir_item")


		let link = createElement('a');// both icon and title, display:flex
		link.href = r_;
		link.title = name;

		link.classList.add('all_link');
		link.classList.add("disable_selection")
		let l_icon = createElement("span")
		// this will go inside "link" 1st
		l_icon.classList.add("link_icon")

		let l_box = createElement("span")
		// this will go inside "link" 2nd
		l_box.classList.add("link_name")


		if (r.startsWith('d')) {
			// add DOWNLOAD FOLDER OPTION in it
			// TODO: add download folder option by zipping it
			// currently only shows folder size and its contents
			type = "folder"
			folder = true
			l_icon.innerHTML = "📂".toHtmlEntities();
			l_box.classList.add('link');
		}
		if (r.startsWith('v')) {
			// if its a video, add play button at the end
			// that will redirect to the video player
			// clicking main link will download the video instead
			type = 'video';
			l_icon.innerHTML = '🎥'.toHtmlEntities();
			link.href = go_link("vid", r_)
			l_box.classList.add('vid');
		}
		if (r.startsWith('i')) {
			type = 'image'
			l_icon.innerHTML = '🌉'.toHtmlEntities();
			l_box.classList.add('file');
		}
		if (r.startsWith('f')) {
			type = 'file'
			l_icon.innerHTML = '📄'.toHtmlEntities();
			l_box.classList.add('file');
		}
		if (r.startsWith('h')) {
			type = 'html'
			l_icon.innerHTML = '🔗'.toHtmlEntities();
			l_box.classList.add('html');
		}

		link.appendChild(l_icon)

		l_box.innerText = " " + name;

		if(s_li[i]){
			l_box.appendChild(createElement("br"))

			let s = createElement("span")
			s.className= "link_size"
			s.innerText = s_li[i]
			l_box.appendChild(s)
		}
		link.appendChild(l_box)


		link.oncontextmenu = function(ev) {
			ev.preventDefault()

			context_menu.show_menus(r_, name, type);
			return false;
		}

		item.appendChild(link);
		//item.appendChild(context);
		// recycling option for the files and folder
		// files and folders are handled differently
		var xxx = "F"
		if (r.startsWith('d')) {
			xxx = "D";
		}


		let hrr = createElement("hr")
		item.appendChild(hrr);
		if (folder) {
			folder_li.appendChild(item);
		} else {
			file_li.appendChild(item)
		}
	});

	clear_file_list(); // clear the links since they are no js compatible

	let dir_container = byId("js-content_list")
	dir_container.appendChild(folder_li)
	dir_container.appendChild(file_li)
}

