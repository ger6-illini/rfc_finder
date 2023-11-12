$(document).ready(function(){
  // this dictionary will help to provide a tooltip with meaning of
  // IETF area abbreviations when/if they are displayed in results
  var dictAreas = {
    "art": "Applications and Real-Time Area",
    "gen": "General Area",
    "int": "Internet Area",
    "ops": "Operations and Management Area",
    "rai": "Real-Time Applications and Infrastructure Area (Concluded)",
    "rtg": "Routing Area",
    "sec": "Security Area",
    "tsv": "Transport Area"
  }

  var activeDivId = $('.nav-link.active').data('target')

  // to clear local storage
  // chrome.storage.local.clear(function() {
  //   var error = chrome.runtime.lastError;
  //   if (error) {
  //       console.error(error);
  //   }
  // });
  // chrome.storage.sync.clear(); // callback is optional

  // save last successful search in local storage
  // so we can load it next time extension is opened
  chrome.storage.local.get(["q"]).then((result) => {
    $("#searchBox").val(result.q);
  });
  chrome.storage.local.get(["resultsHtml"]).then((result) => {
    if (result.resultsHtml) {
      $("#searchResults").removeClass("vh-100"); // large content to be added
    }
    $("#searchResults").html(result.resultsHtml);
  });

  // this is the global variable that will hold the RFC doc-id if URL
  // of active tab contains an RFC coming from the RFC-editor website
  var docid = null;

  // get the current active tab
  chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
    // tabs[0] contains information about the active tab
    if (tabs && tabs[0]) {
      // get the URL of the active tab
      var url = tabs[0].url;
      $("#topics").addClass("vh-100"); // small content to be added
      $("#topics").html("Fetching topics from URL " + url + "...");

      var re = new RegExp("^https://www\.rfc\-editor\.org/rfc/(rfc\\d{4})\.(txt|html)$");
      results = url.match(re)
      if (results) {
        // URL of active tab contains an RFC coming
        // from the RFC-editor website! disable the Topics tab
        docid = results[1].toUpperCase();
      }
      else {
        // URL of active tab does not contain an RFC coming
        // from the RFC-editor website... disable the Topics tab
        $("#nav-link-topics").addClass("disabled");
      }
    }
  });

  // flag to indicate topics were already fetched
  topicsFetched = false;

  $(".nav-link").bind( "click", function(event) {
    event.preventDefault();

    var clickedNavLink = $(this);
    var activeNavLink = $(".nav-link.active");

    // scroll to top
    document.body.scrollTop = document.documentElement.scrollTop = 0;

    // deactivate active nav-link and hide corresponding div
    activeNavLink.removeClass("active");
    var targetActiveDivId = activeNavLink.data('target');
    $("#" + targetActiveDivId).hide();

    // activate the clicked nav-link and unhide corresponding div
    clickedNavLink.addClass("active");
    var targetClickedDivId = clickedNavLink.data('target');
    $("#" + targetClickedDivId).show();

    if (clickedNavLink.data('target') === "topics" && !topicsFetched) {
      loadTopics();
    }
  });

  $("#searchBox").focus();

  // bind a keyup event handler to the search input
  $("#searchBox").on("keyup", function(event) {
    // check if key pressed is Enter (key code 13)
    if (event.keyCode == 13) {
      var searchQuery = $(this).val();

      // make API request to backend
      $.ajax({
        url: "http://127.0.0.1:5000/search",
        method: "GET",
        data: { q: searchQuery },
        dataType: "json",
        success: function(data) {
          // handling the API response and displaying the results
          var resultsHtml = "";
          $("#searchResults").html(resultsHtml);
          if (data.results.length > 0) {
            $("#searchResults").removeClass("vh-100"); // large content to be added
            $.each(data.results, function(index, item) {
              newP = document.createElement("p");
              newP.className = "fs-6";
              newP.setAttribute("id", "result" + index++);
              // section 1: add link to url described by `[doc-id]`" "`title`
              resultsHtml = "<a href=\"" + item.url + "\" target=\"_blank\">[" + item["doc-id"] + "] " + item.title + "</a><br>";
              // section 2: add year
              resultsHtml += "<span class=\"text-success\"><small>" + item.year
              // section 2: add authors
              resultsHtml += "&nbsp;&nbsp;&nbsp;&nbsp;" + item.authors + "</small></span><br>";
              // section 3: add first characters of abstract (if present)
              if (item.abstract !== "") {
                resultsHtml += "<span><small>";
                resultsHtml += item.abstract.length >= 240 ? item.abstract.slice(0, 220) + "..." : item.abstract;
                resultsHtml += "</small></span><br>";
              }
              // section 4: add score
              resultsHtml += "<span class=\"text-muted\"><small>";
              resultsHtml += "score: " + item.score.toFixed(4);
              resultsHtml += "</small></span>";
              // section 4: add pages
              resultsHtml += "<span class=\"text-muted\"><small>";
              resultsHtml += "&nbsp;&nbsp;&nbsp;&nbsp;" + item.pages + " pp.";
              resultsHtml += "</small></span>";
              // section 4: add status
              resultsHtml += "<span class=\"text-muted\"><small>";
              resultsHtml += "&nbsp;&nbsp;&nbsp;&nbsp;status: " + item.status.toLowerCase();
              resultsHtml += "</small></span>";
              // section 4: add area (if present)
              if(item.area !== "") {
                resultsHtml += "<span class=\"text-muted\" title=\"" + dictAreas[item.area] + "\"><small>";
                resultsHtml += "&nbsp;&nbsp;&nbsp;&nbsp;area: " + item.area;
                resultsHtml += "</small></span>";
              }
              // section 4: add wg (if present)
              if(item.wg !== "") {
                resultsHtml += "<span class=\"text-muted\"><small>";
                resultsHtml += "&nbsp;&nbsp;&nbsp;&nbsp;wg: " + item.wg.toLowerCase();
                resultsHtml += "</small></span>";
              }
              // section 4: add stream (if present)
              if(item.stream !== "") {
                resultsHtml += "<span class=\"text-muted\"><small>";
                resultsHtml += "&nbsp;&nbsp;&nbsp;&nbsp;stream: " + item.stream;
                resultsHtml += "</small></span>";
              }
              newP.innerHTML = resultsHtml;
              $("#searchResults").append(newP);
            });
            // store session state after a successful non-empty query
            chrome.storage.local.set({ q: searchQuery });
            chrome.storage.local.set({ resultsHtml: $("#searchResults").html() });
          } else {
            $("#searchResults").addClass("vh-100"); // small content to be added
            var resultsHtml = "<p class='text-danger fs-5'>";
            resultsHtml += "No results containing all your query terms were found. ";
            resultsHtml += "Try more general, fewer, or different keywords and ";
            resultsHtml += "make sure they are all spelled correctly.";
            $("#searchResults").html(resultsHtml);
          }
        },
        error: function(error) {
          $("#searchResults").addClass("vh-100"); // small content to be added
          var resultsHtml = "<p class='text-danger fs-5'>";
          resultsHtml += "Oops! It seems the backend is broken.";
          $("#searchResults").html(resultsHtml);
          console.log("API request failed: " + error);
        }
      });
    }
  });

  // make API call to recover topics data, get the results, and
  // populate all the right HTML elements with those results
  function loadTopics() {
    // make AJAX call
    $.ajax({
      url: "http://127.0.0.1:5000/topics",
      method: "GET",
      data: { docid: docid },
      dataType: "json",
      success: function(data) {
        // handling the API response and displaying the results
        var resultsHtml = "";
        $("#topics").html(resultsHtml);
        var num_topics = Object.keys(data.topics).length;
        if (num_topics > 0) {
          // one or more topics

          $("#topics").removeClass("vh-100"); // large content to be added

          // section 1: topics
          var k = data.k;
          resultsHtml += "<p fs-6>Top " + num_topics + " topics discovered in [" + docid + "] using k = " + k + ". Click on each to see further insights!</p>";
          resultsHtml += "<div class=\"btn-group\" role=\"group\" aria-label=\"Top k topics toggle button group\">";
          var selectFirst = true;  // used to select first radio button
          for (const [key, value] of Object.entries(data.topics)) {
            resultsHtml += "<input type=\"radio\" class=\"btn-check\" name=\"btntopic\" id=\"btn-" + key + "\" autocomplete=\"off\"" + (selectFirst ? " checked" : "") + ">";
            resultsHtml += "<label class=\"btn btn-outline-primary\" for=\"btn-" + key + "\">" + key.toUpperCase() + " (" + (100 * value).toFixed(4) + "%)</label>";
            selectFirst = false;
          }
          resultsHtml += "</div>";

          // section 2: words
          selectFirst = true;  // used to not hide first div
          var num_words = 0;
          for (const [key, value] of Object.entries(data.words)) {
            resultsHtml += "<div class=\"my-3\" id=\"words-" + key + "\"" + (selectFirst ? "" : " style=\"display:none;\"") + ">";
            num_words = data.words[key].length;
            resultsHtml += "<p fs-6>Top " + num_words + " words in topic " + key.toUpperCase() + ":</p>";
            resultsHtml += "</div>";
            selectFirst = false;
          }

          // section 3: docs
          selectFirst = true;  // used to not hide first div
          var num_docs = 0;
          for (const [key, value] of Object.entries(data.docs)) {
            resultsHtml += "<div my-3 id=\"docs-" + key + "\"" + (selectFirst ? "" : " style=\"display:none;\"") + ">";
            num_docs = data.docs[key].length;
            resultsHtml += "<p fs-6>Top " + num_docs + " documents having " + key.toUpperCase() + " as the dominant topic:</p>";
            $.each(data.docs[key], function(index, item) {
              resultsHtml += "<p fs-6 id=\"" + key + "-" + "doc" + index++ + "\">";
              // section 1: add link to url described by `[doc-id]`" "`title`
              resultsHtml += "<a href=\"" + item.url + "\" target=\"_blank\">[" + item["doc-id"] + "] " + item.title + "</a><br>";
              // section 2: add year
              resultsHtml += "<span class=\"text-success\"><small>" + item.year
              // section 2: add authors
              resultsHtml += "&nbsp;&nbsp;&nbsp;&nbsp;" + item.authors + "</small></span><br>";
              // section 3: add first characters of abstract (if present)
              if (item.abstract !== "") {
                resultsHtml += "<span><small>";
                resultsHtml += item.abstract.length >= 240 ? item.abstract.slice(0, 220) + "..." : item.abstract;
                resultsHtml += "</small></span><br>";
              }
              // section 4: add score
              resultsHtml += "<span class=\"text-muted\"><small>";
              resultsHtml += "topic coverage: " + item.score.toFixed(4);
              resultsHtml += "</small></span>";
              // section 4: add pages
              resultsHtml += "<span class=\"text-muted\"><small>";
              resultsHtml += "&nbsp;&nbsp;&nbsp;&nbsp;" + item.pages + " pp.";
              resultsHtml += "</small></span>";
              // section 4: add status
              resultsHtml += "<span class=\"text-muted\"><small>";
              resultsHtml += "&nbsp;&nbsp;&nbsp;&nbsp;status: " + item.status.toLowerCase();
              resultsHtml += "</small></span>";
              // section 4: add area (if present)
              if(item.area !== "") {
                resultsHtml += "<span class=\"text-muted\" title=\"" + dictAreas[item.area] + "\"><small>";
                resultsHtml += "&nbsp;&nbsp;&nbsp;&nbsp;area: " + item.area;
                resultsHtml += "</small></span>";
              }
              // section 4: add wg (if present)
              if(item.wg !== "") {
                resultsHtml += "<span class=\"text-muted\"><small>";
                resultsHtml += "&nbsp;&nbsp;&nbsp;&nbsp;wg: " + item.wg.toLowerCase();
                resultsHtml += "</small></span>";
              }
              // section 4: add stream (if present)
              if(item.stream !== "") {
                resultsHtml += "<span class=\"text-muted\"><small>";
                resultsHtml += "&nbsp;&nbsp;&nbsp;&nbsp;stream: " + item.stream;
                resultsHtml += "</small></span>";
              }
              resultsHtml += "</p>";
            });
            resultsHtml += "</div>";
            selectFirst = false;
          }

          $("#topics").html(resultsHtml);

          // time to add D3 lollipop charts for terms probability
          // inspired by https://d3-graph-gallery.com/lollipop.html

          // set the dimensions and margins of the graph
          const margin = {top: 10, right: 40, bottom: 40, left: 100},
          width = 750 - margin.left - margin.right,
          height = 300 - margin.top - margin.bottom;
          // set duration of transitions
          const duration = 2000;
          var xMax = {};

          for (const [key, wordsData] of Object.entries(data.words)) {

            // append the svg object to the words div
            const svg = d3.select("#words-" + key)
            .append("svg")
            .attr("id", "words-svg-" + key)
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .append("g")
            .attr("transform",
                  `translate(${margin.left}, ${margin.top})`);

            // sort wordsData
            wordsData.sort(function(b, a) {
              return a.p - b.p;
            });

            // Add X axis
            xMax[key] = d3.max(wordsData, function(d) { return +d.p;} );
            const x = d3.scaleLinear()
            .domain([0, xMax[key]])
            .range([ 0, width]);
            svg.append("g")
            .attr("transform", `translate(0, ${height})`)
            .call(d3.axisBottom(x))

            // Add the text label for the x axis
            svg.append("text")
            .attr("transform", "translate(" + (width / 2) + " ," + (height + margin.bottom - 4) + ")")
            .style("text-anchor", "middle")
            .text("Term Probability")

            // Y axis
            const y = d3.scaleBand()
            .range([ 0, height ])
            .domain(wordsData.map(function(d) { return d.word; }))
            .padding(1);
            svg.append("g")
            .call(d3.axisLeft(y))
            .selectAll("text")
            .attr("font-family","monospace")

            // Lines
            svg.selectAll("myline")
            .data(wordsData)
            .join("line")
            // .attr("x1", function(d) { return x(d.p); })
            .attr("x1", x(0))
            .attr("x2", x(0))
            .attr("y1", function(d) { return y(d.word); })
            .attr("y2", function(d) { return y(d.word); })
            .attr("stroke", "#13294B")

            // Circles
            svg.selectAll("mycircle")
            .data(wordsData)
            .join("circle")
            // .attr("cx", function(d) { return x(d.p); })
            .attr("cx", x(0))
            .attr("cy", function(d) { return y(d.word); })
            .attr("r", "7")
            .style("fill", "#E84A27")
            .attr("stroke", "#13294B")
            .append('title')
            .text(function(d) { return `p = ${d.p}`; })

            // Change the X coordinates of line and circle
            svg.selectAll("circle")
              .transition()
              .duration(duration)
              .attr("cx", function(d) { return x(d.p); })

            svg.selectAll("line")
              .transition()
              .duration(duration)
              .attr("x1", function(d) { return x(d.p); })

          }

          // attach handler to dynamically created buttons
          $(".btn-check").on("click", function(event) {
            // hide all divs
            for (const [key, value] of Object.entries(data.topics)) {
              $("#words-" + key).hide();
              $("#docs-" + key).hide();
              const svg = d3.select("#words-svg-" + key)
              // Change the X coordinates of line and circle back to zero
              svg.selectAll("circle")
                .attr("cx", 0)
              svg.selectAll("line")
                .attr("x1", 0)
            }

            // show the div for the topic tied to the button clicked
            var topic = $(this).attr("id").slice(4);
            $("#words-" + topic).show();
            $("#docs-" + topic).show();
            // Add X axis
            const x = d3.scaleLinear()
            .domain([0, xMax[topic]])
            .range([ 0, width]);
            const svg = d3.select("#words-svg-" + topic)
            // Change the X coordinates of line and circle back to zero
            svg.selectAll("circle")
              .transition()
              .duration(duration)
              .attr("cx", function(d) { return x(d.p); })
            svg.selectAll("line")
              .transition()
              .duration(duration)
              .attr("x1", function(d) { return x(d.p); })
          });

          // raise the flag so no need to make another API call to recover
          // the topics for the given docid
          topicsFetched = true;
        } else {
          $("#topics").addClass("vh-100"); // small content to be added
          // topics dictionary has no entries
          var resultsHtml = "<p class='text-danger fs-5'>";
          resultsHtml += "No topics found for [" + docid + "]. ";
          resultsHtml += "Try updating the corpus and rediscover ";
          resultsHtml += "the topics.";
          $("#topics").html(resultsHtml);
        }
      },
      error: function(error) {
        $("#topics").addClass("vh-100"); // small content to be added
        var resultsHtml = "<p class='text-danger fs-5'>";
        resultsHtml += "Oops! It seems the backend is broken.";
        $("#topics").html(resultsHtml);
        console.log("API request failed: " + error);
      }
    });
  }
});
