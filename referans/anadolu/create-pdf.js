var PDFExport = function (Questions, vizeFinal, unite, courseCode,courseName) {

    console.log("pdf1");
    // var questions='';
    //
    // for (var i = 0; i < Questions.length; i++) {
    //
    //     var question='';
    //     question+= wrap('p',Questions[i].Text);
    //     question+=wrap('p',Questions[i].A);
    //     question+=wrap('p',Questions[i].B);
    //     question+=wrap('p',Questions[i].C);
    //     question+=wrap('p',Questions[i].D);
    //     question+=wrap('p',Questions[i].E);
    //     question=wrap('div',question);
    //
    //     questions+=question;
    // }

    var headerr = courseCode + ' - '+courseName+' \n';
    if (vizeFinal) {
        if (vizeFinal == '1') {
            headerr += 'Ara Sınav Deneme Sınavı';
        } else {
            headerr += 'Dönem Sonu Deneme Sınavı';
        }

    } else if (unite) {
        headerr += 'Ünite '+unite + ' - Alıştırma Soruları';
    }

    var footer= 'Anadolu Üniversitesi tarafından hazırlanmış olan bu testlerin her hakkı saklıdır. Hangi amaçla olursa olsun, testlerin tamamının veya bir kısmının Anadolu Üniversitesi\'nin yazılı izni olmadan kopya edilmesi, fotoğraflarının çekilmesi, herhangi bir yolla çoğaltılması ya da kullanılması yasaktır. Bu yasağa uymayanlar gerekli cezai sorumluluğu ve testlerin hazırlanmasındaki mali külfeti peşinen kabullenmiş sayılır.';

    var dd = {

        content: [
            {text: headerr + '\n\n', style: 'header2'}
        ],
        styles: {
            header: {
                fontSize: 16,
                bold: true
            },
            bigger: {
                fontSize: 15,
                italics: true
            },
            header2: {
                fontSize: 18,
                bold: true,
                alignment: 'center'
            },
            footer: {
                fontSize: 7,
                margin: [70, 0, 70, 150]
            }
        },
        background: [
            {
                image: 'data:image/png;base64,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AICgAgBAUAEACCoAAEEFACCoAAAQVAAAggoAQFABAAgqAAAEFQCAoAIAEFQAAIIKAABBBQAgqAAABBUAgKACAEBQAQAIKgAAQQUAIKgAABBUAACCCgBAUAEACCoAAAQVAICgAgAQVAAAggoAAEEFACCoAAAEFQCAoAIAQFABAAgqAABBBQAgqAAAEFQAAIIKAEBQAQAIKgAABBUAgKACABBUAACCCgBAUAEAIKgAAAQVAICgAgAQVAAACCoAAEEFACCoAAAEFQAAggoAQFABAAgqAABBBQCAoAIAEFQAAIIKAEBQAQAgqAAABBUAgKACABBUAAAIKgAAQQUAIKgAAAQVAACCCgBAUAEACCoAAEEFAICgAgAQVAAAggoAQFABACCoAAAEFQCAoAIAEFQAAAgqAABBBQAgqAAABBUAgKACAEBQAQAIKgAAQQUAIKgAABBUAACCCgBAUAEACCoAAAQVAICgAgAQVAAAggoAAEEFACCoAAAEFQCAoAIAQFABAAgqAABBBQAgqAAAEFQAAIIKAEBQAQAIKgAABBUAgKACABBUAACCCgAAQQUAIKgAAAQVAICgAgBAUAEACCoAAEEFACCoAAAQVAAAggoAQFABAAgqAAAEFQCAoAIAEFQAAIIKAEBQAQAgqAAABBUAgKACABBUAAAIKgAAQQUAIKgAAAQVAACCCgBAUAEACCoAAEEFAICgAgAQVAAAggoAQFABACCoAAAEFQCAoAIAEFQAAAgqAABBBQAgqAAABBUAAIIKAEBQAQAIKgAAQQUAgKACABBUAACCCgBAUAEAIKgAAAQVAICgAgAQVAAACCoAAEEFACCoAAAEFQCAoAIAQFABAAgqAABBBQAgqAAAmJ//X4ABAMvC581UKiE/AAAAAElFTkSuQmCC',
                //width: 792
            }
        ],
        header: '',

        footer:{text: footer , style: 'footer'}
    };

    for (var i = 0; i < Questions.length; i++) {
        dd.content.push(getSoru(Questions[i], i + 1));
    }


    var answers = '\n\n\nSıra-Cevap-(Soruid)  ';
    for (var i = 0; i < Questions.length; i++) {
        answers += (i + 1).toString() + '-' + Questions[i].CorrectAnswer + '-('+Questions[i].QuestionId + ')  ';
    }
    answers+='\n*Geri bildirimlerinizi soruid bildirerek yapınız.'

    dd.content.push({text: answers, fontSize: 7, margin: [30,5]});


    if (!vizeFinal) {
        vizeFinal = '';
    }
    if (!unite) {
        unite = '';
    }


    pdfMake.createPdf(dd).download(courseCode + vizeFinal + unite + '.pdf');

};

var getSoru = function (question, num) {

    var text = [];
    text.push({text: num + ' ) ', fontSize: 11, bold: true});
    text.push({text: stripHtml(unescape(question.Text)) + '\n\n',fontSize: 11});
    text.push({text: 'A ) ', fontSize: 11, bold: true});
    text.push({text: stripHtml(unescape(question.A)) + '\n',fontSize: 11});
    text.push({text: 'B ) ', fontSize: 11, bold: true});
    text.push({text: stripHtml(unescape(question.B)) + '\n',fontSize: 11});
    text.push({text: 'C ) ', fontSize: 11, bold: true});
    text.push({text: stripHtml(unescape(question.C)) + '\n',fontSize: 11});
    text.push({text: 'D ) ', fontSize: 11, bold: true});
    text.push({text: stripHtml(unescape(question.D)) + '\n',fontSize: 11});
    text.push({text: 'E ) ', fontSize: 11, bold: true});
    text.push({text: stripHtml(unescape(question.E)) + '\n\n',fontSize: 11});

    // [left, top, right, bottom]
    return {text: text, unbreakable: true,margin:[30,5]};
};


function stripHtml(html) {
    // Create a new div element
    var temporalDivElement = document.createElement("div");
    // Set the HTML content with the providen
    temporalDivElement.innerHTML = html;
    // Retrieve the text property of the element (cross-browser support)
    return temporalDivElement.textContent || temporalDivElement.innerText || "";
}


function stripPTag(html) {

    if (html.startsWith("<p>") && html.endsWith("</p>")){
        return html.slice(3,html.length-4);
    }else{
        return html;
    }


}






var wrap = function (tag, elem) {
    if (tag == 'div') {

        return '<div style="background-color:lightblue">' +
            elem +
            '</div>';

    }

    return "<" + tag + ">" + elem + "</" + tag + ">";
};



//let download = require('./download');


function downloadFile(Questions, vizeFinal, unite, courseCode,courseName,baseUrl,Authorization,RandPart, url) {
   // let url = `https://www.googleapis.com/drive/v2/files/${fileId}?alt=media`;

    // console.log(RandPart, url)

    return fetch(url, {
        method: 'GET',
        headers: {
            'Authorization': Authorization
        }
    }).then(function(resp) {
        return resp.blob();
    }).then(function(blob) {
        download(blob);
    }).catch(function(error) {
        console.log("err : ",error);
        PDFExport(Questions, vizeFinal, unite, courseCode,courseName);
    });
}

var PDFExport2=function(Questions, vizeFinal, unite, courseCode,courseName,baseUrl,Authorization,RandPart,typefilika){
    var testCode=getStr(vizeFinal, unite, courseCode);

    var apipart="sinavapi";

    if (typefilika){
        apipart="v2filikaapi";
    }

    var urll=baseUrl+'/'+apipart+'/examservice/getpdf/'+testCode+"/"+RandPart;

    console.log("pdf2");
    downloadFile(Questions, vizeFinal, unite, courseCode,courseName,baseUrl,Authorization,RandPart, urll);



    //
    // $.ajax({
    //     type: 'GET',
    //
    //     xhrFields: {
    //         responseType: 'blob'
    //     },
    //
    //
    //
    //
    //     url: urll,
    //
    //
    //
    //
    //     headers: {
    //         "Authorization": Authorization
    //     },
    //
    //
    //
    //     success: function (data) {
    //
    //         console.log("!!!!!!!!!!;)");
    //
    //
    //         var url = window.URL.createObjectURL(data);
    //
    //         window.open(url);
    //
    //
    //     },
    //
    //
    //
    //     error: function (ret) {
    //         console.log("err: ",ret);
    //         PDFExport(Questions, vizeFinal, unite, courseCode,courseName);
    //
    //     }
    // });






};







var PDFExport3=function(Questions, vizeFinal, unite, courseCode,courseName,baseUrl,Authorization,RandPart,typefilika){
    var testCode=getStr(vizeFinal, unite, courseCode);

    var apipart="sinavapi";

    if (typefilika){
        apipart="v2filikaapi";
    }

    var urll=baseUrl+'/'+apipart+'/examservice/getpdf/'+testCode+"/"+RandPart+"?withsolution=1";

    console.log("pdf3");
    downloadFile(Questions, vizeFinal, unite, courseCode,courseName,baseUrl,Authorization,RandPart, urll);

};








var getStr=function (vizeFinal, unite, courseCode) {

    var res="";
    if (vizeFinal) {
        res="createvizefinal-20-"+courseCode+"-"+vizeFinal;

    } else if (unite) {
        res="create-10-"+courseCode+"-"+unite;
    }else if (courseCode==="TARIM"){
        res="TARIM"
    }

    return res;


};




let CheckQuestions=function(Questions,courseCode){


    if (courseCode==='TARIM'){
        return true;
    }

    let im='<img src="https://ets.anadolu.edu.tr/storage/nfs/questions/';
    for (let i = 0; i < Questions.length; i++) {


        if (Questions[i].Text.includes(im)  || Questions[i].A.includes(im) ||
            Questions[i].B.includes(im) || Questions[i].C.includes(im) ||
            Questions[i].D.includes(im)  || Questions[i].E.includes(im)   ){

            return true;

        }

    }

    if (courseCode.startsWith("THE")){
        return true;
    }

    let courseList=['TAR111U','TAR112U','ILH1006','ILH2006','TDE205U','TDE206U',
        'TDE103U','TDE104U','TDE302U','TDE401U','ILH2001','ARA1001',
        'ARA1002','ARA2001','ARA2002','TAR229U', 'TDE303U','TDE304U','TARIM'];

    return courseList.includes(courseCode);


};