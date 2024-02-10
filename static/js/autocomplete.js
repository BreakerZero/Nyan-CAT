htmltoshow = document.createElement('span')
htmltoshow.style.opacity = 0.4;
htmltoshow.style.userSelect = "none";
htmltoshow.style.lineHeight = 1.42;
htmltoshow.style.left = 0;
htmltoshow.setAttribute("id", "autocompleter");
histcarettop = 0;
histcaretleft = 0;
htmltoshow.style.position = "absolute";
htmltoshow.style.color = "black";
htmltoshow.style.fontStyle = "normal"
htmltoshow.style.maxWidth= document.getElementsByClassName("ql-editor")[1].getBoundingClientRect().width + "px";
htmltoshow.style.maxHeight= document.getElementsByClassName("ql-editor")[1].getBoundingClientRect().height + "px";
htmltoshow.style.overflow = "hidden";
htmltoshow.style.cursor = "text";
htmltoshow.addEventListener("mouseup", function(e){
    document.getElementsByClassName("ql-editor")[1].focus();
});
function autocompletescript(event){
    lastsection = document.getElementsByClassName("ql-editor")[1].children.length;
    wordinsection = document.getElementsByClassName("ql-editor")[1].children[lastsection -1].textContent.split(/(\s+)/).filter( function(e) { return e.trim().length > 0; });
    l = document.getElementsByClassName("ql-editor")[1].children[lastsection -1].textContent.length;
    lastcar=document.getElementsByClassName("ql-editor")[1].children[lastsection -1].textContent[l-1];
    lenghtofstyle = document.getElementsByClassName("ql-editor")[1].children[lastsection -1].children.length
    var text = document.getElementsByClassName("ql-editor")[1].children[lastsection -1].childNodes[0];
    var range = document.createRange();
    range.selectNode(text);
    var rect = range.getBoundingClientRect();
    leftpos = Math.round(getCaretTopPoint().left) >= Math.round(document.getElementsByClassName("ql-editor")[1].children[lastsection -1].getBoundingClientRect().left + rect.width);
    toppos = Math.round(getCaretTopPoint().top + (document.body.getBoundingClientRect().top - document.getElementsByClassName("ql-editor")[1].getBoundingClientRect().top) + parseInt(window.getComputedStyle(document.getElementsByClassName("ql-editor")[1].children[lastsection -1]).lineHeight, 10))+1>=Math.round(-(document.getElementsByClassName("ql-editor")[1].getBoundingClientRect().top - document.getElementsByClassName("ql-editor")[1].children[lastsection-1].getBoundingClientRect().bottom));
    if (leftpos && toppos || !leftpos && toppos)
    {
        if ( wordinsection[wordinsection.length-1] == null)
        {
            last = " "
        }
        else
        {
            last = wordinsection[wordinsection.length-1];
        }
        if (!last.match(/[.|,|:|;|!|?|"|`|%]/) && lastcar !== ' ') {
            var autocompleterequest = new XMLHttpRequest();
                var url = "/autocomplete";
                autocompleterequest.open("POST", url, true);
                autocompleterequest.setRequestHeader("Content-Type", "application/json");
                autocompleterequest.onreadystatechange = function () {
            if (autocompleterequest.readyState === 4 && autocompleterequest.status === 200)
            {
            var json = JSON.parse(autocompleterequest.responseText);
            answer = json.result;
            toshow = answer.substr(last.length - answer.length);
            htmltoshow.textContent = toshow
            document.body.appendChild(htmltoshow);
            caret = getCaretTopPoint();
            qleditor = document.getElementsByClassName("ql-editor")[1];
            htmltoshow.style.fontSize = window.getComputedStyle(qleditor.children[lastsection -1]).fontSize;
            if (qleditor.children[lastsection -1].children[lenghtofstyle-1] != null)
            {
                htmltoshow.style.fontStyle = window.getComputedStyle(lastrecurelement(qleditor)).fontStyle;
                htmltoshow.style.color = window.getComputedStyle(lastrecurelement(qleditor)).color;
            }
            if(!leftpos && toppos){
                if(parseInt(htmltoshow.style.left) <= parseInt(caret.left))
                {
                    htmltoshow.style.left = caret.left + "px";
                    htmltoshow.style.display = "block";
                }
                else
                {
                    htmltoshow.style.display = "none";
                    histcarettop = 1;
                }
            }
            else
            {
                htmltoshow.style.left = caret.left + "px";
            }
            htmltoshow.style.top = caret.top + "px";
            if(parseInt(htmltoshow.style.left) + parseInt(window.getComputedStyle(htmltoshow).width) >= (document.getElementsByClassName("ql-editor")[1].getBoundingClientRect().right - parseInt(window.getComputedStyle(document.getElementsByClassName("ql-editor")[1], null).paddingLeft)*2))
            {
                htmltoshow.style.display = "none";
            }
            else
            {
                htmltoshow.style.display = "block";
            }
            if(!leftpos && toppos)
            {
                if(parseFloat(htmltoshow.style.left) > parseFloat(caret.left) || parseInt(histcarettop) !== parseInt(caret.top) )
                {
                    htmltoshow.style.left = caret.left + "px";
                    htmltoshow.style.display = "block";
                }
                if(parseFloat(htmltoshow.style.left) < parseFloat(caret.left) && parseInt(histcarettop) === parseInt(caret.top))
                {
                    htmltoshow.style.display = "block";
                    histcarettop = 1;
                }
            }
            if (histcaretleft < caret.left){
                histcaretleft = caret.left;
            }
            if (histcarettop ===1 && histcaretleft ===1){}
            else if(histcarettop===1){
                htmltoshow.style.display = "block";
                if (histcaretleft > caret.left){
                histcarettop = caret.top;
                }

            }
            else{
            histcarettop = caret.top;
            }
            document.body.appendChild(htmltoshow);
            if(caret.left + htmltoshow.getBoundingClientRect().width > qleditor.getBoundingClientRect().right)
            {
                htmltoshow.style.display = "none";
            }
            }
                };
                var data = JSON.stringify({"begin": last});
                autocompleterequest.send(data);
        }
        else
        {
            htmltoshow.textContent = "";
        }
    }
    else
    {
        htmltoshow.textContent = "";
    }
}
document.getElementsByClassName("ql-editor")[1].addEventListener("keydown", clear);
function clear(event) {
    var KeyID = event.keyCode;

    if (typeof qleditor === "undefined") {
        var qleditor = document.getElementsByClassName("ql-editor")[1];
    }
    switch (KeyID) {
        case 8:
            htmltoshow.textContent = "";
            break;
        case 9:
            if ((htmltoshow.textContent !== "") && (htmltoshow.style.display !== "none"))
            {
                if (qleditor.lastChild.innerHTML[qleditor.lastChild.innerHTML.length - 1] === "\t")
                {
                    qleditor.lastChild.innerHTML = qleditor.lastChild.innerHTML.slice(0, -1);
                }
                lastrecurelement(qleditor).insertAdjacentHTML('beforeend', htmltoshow.textContent);
                var range = document.createRange()
                var sel = window.getSelection()
                var len = lastrecurelement(qleditor).childNodes.length
                if (qleditor.children[0].innerText === htmltoshow.textContent)
                {
                    range.setStart(lastrecurelement(qleditor).childNodes[0], htmltoshow.textContent.length)
                }
                else
                {
                    range.setStart(lastrecurelement(qleditor).childNodes[len - 1], 1)
                }
                htmltoshow.textContent = "";
                range.collapse(true)
                sel.removeAllRanges()
                sel.addRange(range)
            }
            break;
        case 13:
            htmltoshow.textContent = "";
            break;
        case 46:
            htmltoshow.textContent = "";
            break;
        default:
            break;
    }
}

function lastrecurelement(t) {
    if (t.lastChild.lastChild === t.lastChild.lastElementChild)
    {
        while(t != null)
        {
            j = t.lastElementChild;
            if (j == null)
            {
                return t;
                break;
            } else
            {
                t = t.lastElementChild
            }
        }
    }
    else {
        return t.lastElementChild
    }
}