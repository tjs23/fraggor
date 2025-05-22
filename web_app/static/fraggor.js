/*jshint esversion: 6 */

//var SITE_SUBDIR = "/cb";
var SITE_SUBDIR = "";

function nav(url) {
    window.location.href = SITE_SUBDIR+url;
}

function remove_children(elem) {
    while (elem.lastElementChild) {
        elem.removeChild(elem.lastElementChild);
    }
}

function update_select(elem, new_options, new_value) {
    let nopts = new_options.length;
    let value;
    if (new_value !== null) {
        value = new_value;
    } else if (elem.value !== null) {
        value = elem.value;
    } else {
        value = null;
    }
    while (elem.length > nopts) {
        elem.removeChild(elem.lastChild);
    }
    while (elem.length < nopts) {
        elem.appendChild(document.createElement('option'));
    }
    let child_opts = elem.options;
    let found_value = null;
    for (let i=0; i<new_options.length; i+=1) {
        child_opts[i].value = new_options[i].value;
        child_opts[i].innerHTML = new_options[i].label;
        if ((value !== null) && (child_opts[i].value == value)) {
            elem.value = value;
            found_value = true;
        }
    }
    if (found_value === null) {
        elem.value = null;
    }
}

function ajax_json_request(url, opts=null, async=true) {

    let json_str;
    
    if (opts !== null) {
       json_str = JSON.stringify(opts);
    } else {
       json_str = JSON.stringify({});
    }
    
    let request = $.ajax({async:async, url:SITE_SUBDIR + url, data:json_str, type:"POST", contentType:"application/json", dataType:'json'});
    return request;
}

function create(prnt, etype, classlist, html) {

    let elem = document.createElement(etype);
    
    if (classlist != null) {
        elem.classList = classlist;
    }
 
    if (html != null) {
        elem.innerHTML = html;
    }
    
    prnt.appendChild(elem);
    return elem;
}

function make_table(db_table, table_name, columns, update_func, table_height, table_width, selectable_rows) {
    
    if (selectable_rows == null) {
        selectable_rows = true;
    }
 
    table_args = {'pagination':true, 'paginationSize':50, 'layout':"fitData",
                  'selectableRows':selectable_rows, 'selectableRowsRangeMode':"click"};
                  
    table_args.columns = columns;
    
    if (table_height != null) {
        table_args.height = table_height;
    }
    if (table_width != null) {
        table_args.width = table_width;
    }
    
    let table = new Tabulator('#' + table_name, table_args);
    
    table.app_config = {'context':null,'db_table':db_table};
    table.app_update = function(context) { if (context) {update_func(context);} else {update_func();} };

    //make_filter_elements(table_name, columns);
    //make_edit_buttons(table_name);
    
    //table.on("rowDblClick", function() {info_table_row(table)});
    
    return table;
}


function hide_modal(ename) {
    if (ename == null) {
        ename = 'popup';
    }
    let popup = document.getElementById(ename);
    popup.style.display='none';
}


function show_modal(html, button_html, close_html) {
    let popup = document.getElementById('popup');
    let div_modal = document.getElementById('div_modal');
    let div_modal_button = document.getElementById('div_modal_button');
    let div_modal_close_button = document.getElementById('div_modal_close_button');
    div_modal.innerHTML = html;
    
    if (button_html != null) {
       div_modal_button.innerHTML = button_html;
    } else {
       div_modal_button.innerHTML = '';
    }
    
    if (close_html != null) {
       div_modal_close_button.innerHTML = close_html;
    } else {
       div_modal_close_button.innerHTML = 'Close';
    }
    
    popup.style.display = 'block';
}


function highlight_empty_elements(elements) {
    
    let element;
    
    for (let i=0; i<elements.length; i+=1) {
        element = elements[i];
        
        if (element.value) {
            element.style.backgroundColor ='#FFF';
        } else {
            element.style.backgroundColor ='#FF0';
        }        
    } 
}

function resize_window() {
    
    let div_top = document.getElementById('div_top');
    let div_main = document.getElementById('div_main');
    let div_bottom = document.getElementById('div_bottom');
    let h = window.innerHeight - div_top.offsetHeight - div_bottom.offsetHeight;
    let w = window.innerWidth - 12;
    let l;
    if (w > 1280) {
        l = (w - 1280)/2;
        w = 1280;
    } else {
        l = 0;
    }

    div_main.style.height = h + 'px';
    div_main.style.width = w + 'px';
    div_main.style.left = l + 'px';     
} 


//  Edit & buttons

function make_edit_buttons(table_name) {
    let div_name = table_name + '_edit';
    let div = document.getElementById(div_name);
    
    while (div.lastElementChild) {
        div.removeChild(div.lastElementChild);
    }
    
    create(div, 'legend', null, 'Selected row');
    
    let info_button = document.createElement("button");
    let new_button = document.createElement("button");
    let edit_button = document.createElement("button");
    let copy_button = document.createElement("button");
    let delete_button = document.createElement("button");

    info_button.id = div_name + '_info_button';
    new_button.id = div_name + '_new_button';
    edit_button.id = div_name + '_edit_button';
    copy_button.id = div_name + '_copy_button';
    delete_button.id = div_name + '_delete_button';
        
    info_button.innerHTML = 'Details';
    new_button.innerHTML = 'New';
    edit_button.innerHTML = 'Edit';
    copy_button.innerHTML = 'Copy';
    delete_button.innerHTML = 'Delete';
    
    let table = Tabulator.findTable("#" + table_name)[0];
  
    info_button.onclick = function () {info_table_row(table);};
    new_button.onclick = function () {edit_table_row(table, true, false);};
    edit_button.onclick = function () {edit_table_row(table, false, false);};
    copy_button.onclick = function () {edit_table_row(table, true, true);}; // (table, new?, copy?)
    delete_button.onclick = function () {pre_delete_table_row(table);};

    info_button.disabled = true;
    new_button.disabled = false;
    edit_button.disabled = true;
    copy_button.disabled = true;
    delete_button.disabled = true;
    
    div.appendChild(info_button);
    div.appendChild(new_button);
    div.appendChild(edit_button);
    div.appendChild(copy_button);
    div.appendChild(delete_button);    
    
}

function make_info_panel(form_data) {

    let info_popup  = document.getElementById('info_popup');
    let info_div = document.getElementById('info_div');
    let edit_data = form_data.edit_data;
    remove_children(info_div);
    
    for (let db_table in edit_data) {
        let data = edit_data[db_table];
        let items = data.items;
        let n = items.length;
        
        // Frame
        
        let edit_frame = create(info_div, "fieldset", 'edit_frame', null);
        let frame_title = data.title;
        if (n>1) {
            frame_title = frame_title + 's';
        } 
        create(edit_frame, "legend", null, frame_title);

        // Inner 
        
        for (k=0; k < n; k+=1) {
             let item = items[k];
             let current_id = item.current_id;
             let edit_items = item.item_data;
             let item_key;

             let inner_div;
             if (n==1) {
                 inner_div = edit_frame;
                 
             } else {
                 inner_div = create(edit_frame, "fieldset", 'edit_inner', null);
                 let inner_legend =  create(inner_div, "legend", null, item.idx);
             }
             
             let table_layout = create(inner_div, "table", null, null);
 
             for (let i=0; i < edit_items.length; i += 1) {
                 let item = edit_items[i];
                 let tr1 = create(table_layout, "tr");
                 let td1 = create(tr1, "td", 'edit_col1', item.label);
                 let td2 = create(tr1, "td", 'info_col2');
                 let elem = create(td2, 'span', 'info_span', item.value);

             }
        }        
    }
    info_popup.style.display='block';
}

function show_required_null(input_element) {

    if (input_element.value) {
        input_element.classList = '';
    } else  {
        input_element.classList = 'needs_value';
    }

}

function regexp_filter_input(event, element, regex) {
    let re = RegExp(regex);
    let val = element.value;
    let allowed = [];
    for (let i=0; i < val.length; i+=1) {
       if (re.test(val[i])) {
           allowed.push(val[i]);
       }
    }
    element.value = allowed.join('');
}

function edit_spread_values(src_elem, elements) {
    
    if (src_elem.type == 'checkbox') {
        for (let j=0; j < elements.length; j +=1) {
            if (elements[j] !== src_elem) {
                elements[j].checked = src_elem.checked;
                show_required_null(elements[j]);
            }
 
        }
    } else {
        for (let j=0; j < elements.length; j +=1) {
            if (elements[j] !== src_elem) {
                elements[j].value = src_elem.value;
                show_required_null(elements[j]);
            }
 
        }
    }
}

function make_edit_form(table, form_data, row_input) {

    let edit_popup  = document.getElementById('edit_popup');
    let edit_div = document.getElementById('edit_div');
    let commit_edit_button = document.getElementById('commit_edit_button');
    let n_del = form_data.delete_data.length;
    let edit_data = form_data.edit_data;
    commit_edit_button.onclick= function() {commit_edit(table);};
    
    let prev_inputs = document.getElementsByClassName("edit_input");
    let prev_values = {};
    
    for (let i=0; i < prev_inputs.length; i+=1) {
        prev_values[prev_inputs[i].id] = prev_inputs[i].value; 
    }
    
    remove_children(edit_div);
    
    for (let i=0; i < n_del; i+=1) {
        let hidden = create(edit_div, "input", 'delete_input');
        hidden.type = 'hidden';
        hidden.value = form_data.delete_data[i];
    }
    
    for (let db_table in edit_data) {
        let data = edit_data[db_table];
        let items = data.items;
        let n = items.length;
        
        // Frame
        
        let edit_frame = create(edit_div, "fieldset", 'edit_frame', null);
        let legend = document.createElement("legend");
        let frame_title = data.title;
        if (n>1) {
            frame_title = frame_title + 's';
        } 
        
        if (items[0].current_id) {
            legend.innerHTML = frame_title;
        } else {
            legend.innerHTML = 'New ' + frame_title;   
        }
        edit_frame.appendChild(legend);
        
        // Inner 
        
        let elements = {};
        
        for (k=0; k < n; k+=1) {
             let item = items[k];
             let current_id = item.current_id;
             let edit_items = item.item_data;
             let item_key;
 
             if (current_id) {
                 row_key = db_table + '|' + current_id + '|';
             } else {
                 row_key = db_table + '|#' + k + '|';
             }
             
             let inner_div;
             if (n==1) {
                 inner_div = edit_frame;
             } else {
                 inner_div = create(edit_frame, "fieldset", 'edit_inner', null);
                 let inner_legend =  create(inner_div, "legend", null, item.idx);
             }
             
             let table_layout = create(inner_div, "table", null, null);
 
             for (let i=0; i < edit_items.length; i += 1) {
                 let item = edit_items[i];
                 let eid = row_key + item.key;
                 
                 if (eid in prev_values) {
                     item.value = prev_values[eid];
                 }
                 
                 if (item.itype == 'hidden') {
                     let elem = create(edit_div, 'input', 'edit_input', null);
                     elem.id = eid;
                     elem.type = item.itype;
                     elem.value = item.value;
 
                 } else {
                     let tr1 = document.createElement("tr");
                     table_layout.appendChild(tr1);
 
                     let td1 = document.createElement("td");
                     let td2 = document.createElement("td");
                     tr1.appendChild(td1);
                     tr1.appendChild(td2);
 
                     td1.innerHTML = item.label;
                     let elem = document.createElement(item.element);
                     elem.id = eid;
                     elem.classList = 'edit_input';
 
                     if (item.required) {
                         td1.classList = 'edit_col1 is_required';
                         elem.oninput = function() {show_required_null(elem);};
                     } else {
                         td1.classList = 'edit_col1';
                     }
                     td2.classList = 'edit_col2';
 
                     if (item.element == 'textarea') {
                          let tr2 = document.createElement("tr");
                          table_layout.appendChild(tr2);
 
                          let td3 = document.createElement("td");
                          td3.colSpan = 2;
                          tr2.appendChild(td3);
                          td3.appendChild(elem);
 
                     } else {
                          td2.appendChild(elem);
 
                          if (item.element == 'input') {
                              elem.type = item.itype;
                          }
                          
                          if (item.itype == 'time') {
                              let time_select = document.createElement("select");
                              td2.appendChild(time_select);
                              time_select.classList = 'time'
                              
                              let time_opts = [{'value':'', 'label':'&#9202;'}]
                              
                              for (let t=9; t<17; t+=1) {
                                  let val;
                                  
                                  if (t < 10) {
                                     val = '0' + t + ':00';
                                     val2 = '0' + t + ':30';
                                  } else {
                                     val = t + ':00';
                                     val2 = t + ':30';
                                  }
                                     
                                  time_opts.push({'value':val, 'label':val});
                                  time_opts.push({'value':val2, 'label':val2});
                              }
                              
                              update_select(time_select, time_opts, '');
                              time_select.onchange = function() {elem.value = time_select.value;
                                                                 time_select.value = '';
                                                                 show_required_null(elem);};
                          
                          }
                          
                     }
 
                     if (item.element == 'select') {
                         update_select(elem, item.options, item.value);
 
                     } else if (item.value != null) {
                         if (item.itype == 'checkbox') {
                             elem.value = 'check';
                             elem.checked = Boolean(item.value) == true;
 
                         } else {
                             elem.value = item.value;
                         }
                     }
                     if (item.regex) {
                         elem.onkeyup = function(event) { regexp_filter_input(event, elem, item.regex);};
                         elem.onblur = function(event) { regexp_filter_input(event, elem, item.regex);};
                     }

                     if (item.required) {
                         show_required_null(elem);
                     }
 
                     for (let arg_name in item.args) {
                         elem[arg_name] = item.args[arg_name];
                     }
 
                     elem.required = item.required;
 
                     if (i in elements) {
                         elements[i].push(elem);
                     } else {
                         elements[i] = [elem];
                     }
                     
                     if (n > 1) {
                         let set_all =  document.createElement("button");
                         set_all.innerHTML = "&#11109;";
                         set_all.classList = 'all_same';
                         set_all.title = "Set all equivalent items to this value";
                         td2.appendChild(set_all);                        
                         set_all.onclick = function() { edit_spread_values(elem, elements[i]) };
                     
                     }
                     
                 }
             }
        }
        
        if (data.items[0].idx != 0) { // child
            let add_btn = create(edit_frame, 'button', 'btn-blue fs13', 'Add ' + data.title);
            add_btn.onclick = function () {alter_edit_child_count(table, row_input, n+1);};
            if (n > 1) {
                let rem_btn = create(edit_frame, 'button', 'btn-blue fs13', 'Remove ' + data.title);
                rem_btn.onclick = function () {alter_edit_child_count(table, row_input, n-1);};
            }
        }
        
    }
    edit_popup.style.display='block';
}


function alter_edit_child_count(table, row_input, n) {
    row_input.nchild = n;
    let request = ajax_json_request('/edit_row/', row_input);
    request.done(function(data) {
        make_edit_form(table, data, row_input);
    });

}

function commit_edit(table) {

    let edit_popup = document.getElementById('edit_popup');
    let edit_inputs = document.getElementsByClassName("edit_input");
    let delete_inputs = document.getElementsByClassName("delete_input");
    let required_ok = true;
    let item_data = {};
    let delete_data = [];
    let user_id = null;
    let activated = null;

    for (let i=0; i < delete_inputs.length ; i += 1) {
        delete_data.push(delete_inputs[i].value);
    }
    
    for (let i=0; i < edit_inputs.length ; i += 1) {
        let elem = edit_inputs[i];
        let eid = elem.id.split('|');
        let current_id = eid[1];
        
        if (current_id && (elem.type == 'hidden')) {
            continue; // Hidden is only for new items
        }
        if (elem.required) {
            show_required_null(elem);
            if  (!elem.value) {
                required_ok = false;
            }
        }
        if (elem.type == 'checkbox') {
            item_data[elem.id] = elem.checked;
            
        } else {
            item_data[elem.id] = elem.value;
        }
        if ((eid[0] == 'GroupMember') && (eid[2] == 'user_id')) {
            user_id = item_data[elem.id];
        }
        if ((eid[0] == 'GroupMember') && (eid[2] == 'is_active') && item_data[elem.id]) {
            activated = true;
        }
        
    }
    
    if ((user_id != null) && (activated != null)){
        pre_activate_user(user_id);  
    }
    
    if (required_ok) { 
        let request = ajax_json_request('/commit_edit/', {'item_data':item_data, 'delete_data':delete_data});        
        request.done(function(data) {
            if (data.msg) {
                show_modal('<h3>Edit Item</h3>' + data.msg);
            }
            if (data.error) {
                show_modal('<h3>Edit Error</h3>' + data.error);
            } else {
                edit_popup.style.display = 'none';
                table.app_update();
            } 
        });
        
    }
}


function pre_delete_table_row(table) {
    let selected_data = table.getSelectedData();
    if (selected_data.length > 0) {
        let db_table = table.app_config.db_table;
        let current_ids = [];
        for (let i=0; i < selected_data.length; i+= 1) {
           current_ids.push(selected_data[i]._id);
        }
        
        let request = ajax_json_request('/pre_delete_rows/', {'current_ids':current_ids, 'db_table':db_table});
        
        request.done(function(data) {
            if (data.msg) {
                let button_html = '<button class="btn-red" id="del_confirm_button">Confirm Delete</button>';
                show_modal('<h3>Delete Item</h3>' + data.msg, button_html, "Cancel");
                let del_confirm_button = document.getElementById('del_confirm_button');
                del_confirm_button.onclick = function() {delete_table_rows(table, db_table, current_ids); hide_modal();};
            }
            if (data.error) {
                show_modal('<h3>Delete Error</h3>' + data.error);
            }
        });
    }

}


function edit_table_row(table, is_new, is_copy) {
    let selected_data = table.getSelectedData();
    let db_table = table.app_config.db_table;
    let json_args;
    let json_url = null;
    let current_id;
    
    if (is_new) {
        if (is_copy && (selected_data.length > 0)) {
            current_id = selected_data[0]._id;
            json_args = {'current_id':current_id, 'db_table':db_table};
          } else {
            json_args = {'db_table':db_table};
            current_id = null;
        }
        json_url = '/is_table_editable/';
    } else if (selected_data.length > 0) {
        current_id = selected_data[0]._id;
        json_args = {'current_id':current_id, 'db_table':db_table};
        json_url = '/is_row_editable/';
    }
        
    if (json_url) {
         let request = ajax_json_request(json_url, json_args);
         request.done(function(data) {
            if (data.editable) {
                let row_ids = {};
                row_ids[db_table] = current_id;
                let row_in = {'row_ids':row_ids, 'copy':is_copy, 'nchild':0};
                let request2 = ajax_json_request('/edit_row/', row_in);
                request2.done(function(data2) {
                    make_edit_form(table, data2, row_in);
                });
 
            } else {
                if (is_new) {
                    show_modal('<h3>New Item Error</h3>Table cannot be edited by the current user.');
                
                } else {
                    show_modal('<h3>Edit Item Error</h3>Row cannot be edited by the current user.');
                }
            }
        });
    }
}

function info_table_row(table) {
    let selected_data = table.getSelectedData();
    if (selected_data.length > 0) {
        let db_table = table.app_config.db_table;
        let current_id = selected_data[0]._id;
        let row_ids = {};
        row_ids[db_table] = current_id;
        
        if (db_table == 'SeqRun') {
            row_ids.SeqLibrary = selected_data[0].lib_id;
        }
        let row_input = {'row_ids':row_ids, 'copy':false, 'info':true, 'nchild':0};
        let request = ajax_json_request('/edit_row/', row_input );
        request.done(function(data) {
            make_info_panel(data);
        });

    }
}

function delete_table_rows(table, db_table, current_ids) {

    let request = ajax_json_request('/delete_rows/', {'current_ids':current_ids, 'db_table':db_table});
    request.done(function(data) {
        if (data.error) {
            show_modal('<h3>Delete Error</h3>' + data.error);
        } else {
            table.app_update();
        }
    });
}

//  Filters

function make_filter_elements(filter_name, columns, table_name) {
    let div = document.getElementById(filter_name + '_filter');
    

    while (div.lastElementChild) {
        div.removeChild(div.lastElementChild);
    }
    
    if (table_name == null) {
        table_name = filter_name;
    }
    create(div, "legend", null, 'Filter rows');
    
    let find_button = document.createElement("button");
    find_button.id = filter_name + '_find_button';
    find_button.innerHTML = 'Find ... ';
    find_button.style.display = 'inline-block';
    div.appendChild(find_button);
    
    let inner_div = document.createElement("div");
    inner_div.id = filter_name + '_inner_div';
    div.appendChild(inner_div);
    
    let field_options = [{'value':'', 'label':'column...'}];
 
    for (let i=0; i < columns.length; i+=1) {
        field_options.push({'label':columns[i].title, 'value':columns[i].field});
    }
   
    let field_select = document.createElement("select");
    field_select.id = filter_name + '_filter_field';
    field_select.required = true;
    field_select.onchange = function() {update_filter(filter_name, table_name);};
    
    let ftype_select = document.createElement("select");
    ftype_select.id = filter_name + '_filter_type';
    ftype_select.onchange = function() {update_filter(filter_name, table_name);};
    
    let value_input = document.createElement("input");
    value_input.id = filter_name + '_filter_value';
    value_input.size = 16;
    value_input.type = 'text';
    value_input.placeholder = "find ... ";
    value_input.onkeyup = function() {update_filter(filter_name, table_name);};
    
    let clear_button = document.createElement("button");
    clear_button.id = filter_name + '_filter_clear';
    clear_button.innerHTML = "&#10006;";
    clear_button.classList = "clear_button";
     
    update_select(ftype_select, [{'value':'like', 'label':'contains'},
                                 {'value':'starts', 'label':'starts with'},
                                 {'value':'=', 'label':'is exactly'},
                                 {'value':'!=', 'label':'is not'}], 'like');
    
    update_select(field_select, field_options, '');
    
    inner_div.appendChild(field_select);
    inner_div.appendChild(ftype_select);
    inner_div.appendChild(value_input);
    inner_div.appendChild(clear_button);
   
    clear_button.onclick = function() {
        field_select.value = "";
        ftype_select.value = "like";
        value_input.value = "";
        inner_div.style.display = 'none';
        find_button.style.display = 'inline-block';
        update_filter(filter_name, table_name);
    };
    
    find_button.onclick = function() {
        find_button.style.display = 'none';
        inner_div.style.display = 'inline-block';
    };
    
    inner_div.style.display='none';
    
}
    
function update_filter(filter_name, table_name) {
    let table = Tabulator.findTable("#"+table_name)[0];
    let field_pulldown = document.getElementById(filter_name + '_filter_field');
    let value_input = document.getElementById(filter_name + '_filter_value');
    let ftype_pulldown = document.getElementById(filter_name + '_filter_type');
    let filters = [];
    if (field_pulldown.value && value_input.value) {
        filters.push({field:field_pulldown.value, type:ftype_pulldown.value, value:value_input.value });
    }   

    if (filters.length > 0) {
        table.setFilter(filters);
    } else {
        table.clearFilter();
    }
}

//


function initialize_main() {
    let request = ajax_json_request('/get_data_cols/', null);
    request.done(function(data) {
        let main_table = make_table('FragDataSet', 'main_table', data.cols, update_main_table, "100%", '100%', true);
        main_table.on("tableBuilt", function() {
                main_table.on("rowClick", select_main_row);
                update_main_table();
        });
    });

}

function select_main_row(event, row) {
    let row_data = row.getData();    
    let request = ajax_json_request('/set_data_id/', {'data_id':row_data.data_id});

}

function update_main_table() {
    let request = ajax_json_request('/get_data_table/', null);    
    request.done(function(data) {
        let table = Tabulator.findTable("#main_table")[0];
        table.replaceData(data.rows);
    });
}

//

function initialize_calc() {
    let request = ajax_json_request('/get_proteome_cols/', null);
    request.done(function(data) {
        let proteome_frame = document.getElementById('proteome_frame');
        proteome_frame.style.display = 'none';
        let proteome_table = make_table('Proteome', 'proteome_table', data.cols, update_proteome_table, "100%", '100%', true);
        proteome_table.on("tableBuilt", function() {
                proteome_table.on("rowClick", select_proteome_row);
                update_proteome_table();
        });
        let codon_set_select = document.getElementById('codon_set_select');
        update_select(codon_set_select, data.codon_sets, data.codon_set);
    });
}

function select_proteome_row(event, row) {
    let row_data = row.getData();
    let selected_proteome = document.getElementById('selected_proteome');
    selected_proteome.innerHTML = row_data.uniprot_id + ' : ' + row_data.species;
    let request = ajax_json_request('/set_proteome/', {'proteome':row_data.uniprot_id});
}

function update_proteome_table() {
    let request = ajax_json_request('/get_proteome_table/', null);    
    request.done(function(data) {
        let table = Tabulator.findTable("#proteome_table")[0];
        table.replaceData(data.rows);
    });
}

function run_taxon_search(taxon) {

    let taxon_entry =  document.getElementById('taxon_input');
    
    if (taxon != null) {
       taxon_entry.value = taxon;
    } else {
       taxon = taxon_entry.value;
    }
       
    if (taxon) {
        let request = ajax_json_request('/search_taxon/', {'taxon': taxon});
        request.done(function(data) {
            if (data.error) {
                show_modal('<h3>Search Error</h3>' + data.error);
            } else {
                let table = Tabulator.findTable("#proteome_table")[0];
                table.replaceData(data.rows);
                let proteome_frame =  document.getElementById('proteome_frame');
                proteome_frame.style.display = 'block';
            }
        });
    }
     
}

function update_submit_status() {
    
    let user_email = document.getElementById('user_email');
    show_required_null(user_email);

}



function run_data_generation() {
    // data_id, proteome, codon_use, pep_len, overlap
    
    selected_proteome = document.getElementById('selected_proteome');
    
    let table = Tabulator.findTable("#proteome_table")[0];
    let selected_data = table.getSelectedData();
    
    update_submit_status();
    
    
    
    if (selected_data && (selected_data.length > 0)) {
    
        let uniprot_id = selected_data[0].uniprot_id;
        let width_entry = document.getElementById('width_entry');
        let overlap_entry = document.getElementById('overlap_entry');
        let codon_set_select = document.getElementById('codon_set_select');
        let user_email = document.getElementById('user_email');
        
        if (!(user_email.value)) {
           show_modal('<h3>Input Error</h3>No email specified');
           
        } else {
            let request = ajax_json_request('/check_generate_data/', {'proteome':uniprot_id,
                                                                      'pep_len':width_entry.value,
                                                                      'overlap':overlap_entry.value,
                                                                      'codon_set':codon_set_select.value,
                                                                      'email':user_email.value});                                                
            request.done(function(data) {
                if (data.error) {
                    show_modal('<h3>Data Generation Error</h3>' + data.error);
                } else {
                    let button_html = '<button class="btn-red" id="confirm_calc_button">OK</button>';
                    show_modal('<h3>Confirm Submission?</h3>' + data.msg, button_html, "Cancel");
                    let confirm_button = document.getElementById('confirm_calc_button');
                    confirm_button.onclick = function() {generate_data(data.params); hide_modal();}
                }
            });
        }
    } else {
        show_modal('<h3>Input Error</h3>No proteome specified');
    }
            
}

function recalculate_data() {
    let table = Tabulator.findTable("#main_table")[0];
    let selected_data = table.getSelectedData();
    
    if (selected_data && (selected_data.length > 0)) {
        let row = selected_data[0];
        let params = {'proteome':row.proteome_id, 'pep_len':row.pep_len, 'overlap':row.overlap,
                      'codon_set':row.codon_use, 'email':'tstevens@mrc-lmb.cam.ac.uk'};
                      
        let request = ajax_json_request('/check_generate_data/', params);                                                
        request.done(function(data) {
            if (data.error) {
                show_modal('<h3>Data Generation Error</h3>' + data.error);
            } else {
                let button_html = '<button class="btn-red" id="confirm_calc_button">OK</button>';
                show_modal('<h3>Confirm Submission?</h3><p>Peptide fragments will be regenerated for proteome ' + row.proteome_id  + '</p>', button_html, "Cancel");
                let confirm_button = document.getElementById('confirm_calc_button');
                confirm_button.onclick = function() {generate_data(data.params); hide_modal();}
            }
        });
    } else {
        show_modal('<h3>Input Error</h3> No dataset selected');
    }
}

function generate_data(params) {    
    let request = ajax_json_request('/generate_data/', params);
    request.done(function(data) {
        nav('/');
    });
}

function download_data() {    
    let seq_type = seq_download_select.value
    let table = Tabulator.findTable("#main_table")[0];
    let selected_data = table.getSelectedData();
    
    if (selected_data && (selected_data.length > 0)) {
        let row = selected_data[0];
        
        if (row.status == 'complete') {
           if (seq_type) {
               nav('/download_data/' + seq_type);
           }
        
        } else {
           show_modal('<h3>Download Error</h3><p>Data generation is not complete for the selected dataset</p>');
        }
        
    
    } else {
        show_modal('<h3>Download Error</h3><p>No dataset selected</p>');
    }
    
}


