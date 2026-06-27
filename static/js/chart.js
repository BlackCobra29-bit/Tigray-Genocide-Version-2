window.onload = function () {
  
  console.log(Math.round({{bar_chart_items_percentage.0}}))

  // Zone Report
        // to increase the maximum X-axis point of the bar chart
            var maxIndexValue = Math.max(
                  {{ line_data_points.0|safe }},
                  {{ line_data_points.1|safe }},
                  {{ line_data_points.2|safe }},
                  {{ line_data_points.3|safe }},
                  {{ line_data_points.4|safe }},
                  {{ line_data_points.5|safe }},
                  {{ line_data_points.6|safe }},
                  {{ line_data_points.7|safe }}
                );
      // end


var chart = new CanvasJS.Chart("chartContainer", {
  animationEnabled: true,
  axisX:{
    interval: 1,
    title: "Tigray Zone"
  },
  axisY2:{
    interlacedColor: "rgba(1,77,101,.2)",
    gridColor: "rgba(1,77,101,.1)",
    title: "Number of Civilian Victims",
    maximum: maxIndexValue + (maxIndexValue/2)
  },
  data: [{
    type: "bar",
    name: "companies",
    axisYType: "secondary",
    color: "#014D65",
    dataPoints: [
      { y: {{ line_data_points.0|safe }}, label: "West", indexLabel: "{y}", indexLabelFontSize: '14', indexLabelPlacement: "outside", markerColor: "red", markerType: "triangle", toolTipContent: "<b>{label}</b>(<i>{{ line_chart_items_percentage.0|safe }}%</i>)" },
      { y: {{ line_data_points.1|safe }}, label: "East", indexLabel: "{y}", indexLabelFontSize: '14', indexLabelPlacement: "outside", markerColor: "red", markerType: "triangle", toolTipContent: "<b>{label}</b>(<i>{{ line_chart_items_percentage.1|safe }}%</i>)" },
      { y: {{ line_data_points.2|safe }}, label: "Central", indexLabel: "{y}", indexLabelFontSize: '14', indexLabelPlacement: "outside", markerColor: "red", markerType: "triangle", toolTipContent: "<b>{label}</b>(<i>{{ line_chart_items_percentage.2|safe }}%</i>)" },
      { y: {{ line_data_points.3|safe }}, label: "North West", indexLabel: "{y}", indexLabelFontSize: '14', indexLabelPlacement: "outside", markerColor: "red", markerType: "triangle", toolTipContent: "<b>{label}</b>(<i>{{ line_chart_items_percentage.3|safe }}%</i>)" },
      { y: {{ line_data_points.4|safe }}, label: "South", indexLabel: "{y}", indexLabelFontSize: '14', indexLabelPlacement: "outside", markerColor: "red", markerType: "triangle", toolTipContent: "<b>{label}</b>(<i>{{ line_chart_items_percentage.4|safe }}%</i>)" },
      { y: {{ line_data_points.5|safe }}, label: "South East", indexLabel: "{y}", indexLabelFontSize: '14', indexLabelPlacement: "outside", markerColor: "red", markerType: "triangle", toolTipContent: "<b>{label}</b>(<i>{{ line_chart_items_percentage.5|safe }}%</i>)" },
      { y: {{ line_data_points.6|safe }}, label: "Mekelle", indexLabel: "{y}", indexLabelFontSize: '14', indexLabelPlacement: "outside", markerColor: "red", markerType: "triangle", toolTipContent: "<b>{label}</b>(<i>{{ line_chart_items_percentage.6|safe }}%</i>)" },
      { y: {{ line_data_points.7|safe }}, label: "Other", indexLabel: "{y}", indexLabelFontSize: '14', indexLabelPlacement: "outside", markerColor: "red", markerType: "triangle", toolTipContent: "<b>{label}</b>(<i>{{ line_chart_items_percentage.7|safe }}%</i>)" }
    ]
  }]
});

chart.render();

  // Age Report
  
  // Get the maximum value among the chart data points
    var maxChartValue = Math.max(
      {{ bar_data_points.0|safe }},
      {{ bar_data_points.1|safe }},
      {{ bar_data_points.2|safe }},
      {{ bar_data_points.3|safe }},
      {{ bar_data_points.4|safe }},
      {{ bar_data_points.5|safe }},
      {{ bar_data_points.6|safe }},
      {{ bar_data_points.7|safe }}
    );

  var chart = new CanvasJS.Chart("chartContainer2", {
    animationEnabled: true,
    theme: "light2", // "light1", "light2", "dark1", "dark2",
    axisY: {
      title: "Number of Civilian Victims",
      gridThickness: 0,
      maximum: maxChartValue + (maxChartValue/2)
    },
    axisX: {
        title: "Age of victims"
    },
    data: [{        
      type: "column",  
      showInLegend: true, 
      legendMarkerColor: "grey",
      indexLabelFontWeight: "bolder",
      legendText: "Civilian Victims report by Age",
      dataPoints: [      
        { y: {{ bar_data_points.0|safe }}, label: "< 10", indexLabel: "{y}", indexLabelFontSize: '12', markerColor: "red", markerType: "triangle", toolTipContent: "<b>{label}</b>(<i>{{ bar_chart_items_percentage.0|safe }}%</i>)" },
        { y: {{ bar_data_points.1|safe }},  label: "10-18", indexLabel: "{y}", indexLabelFontSize: '12', markerColor: "red", markerType: "triangle", toolTipContent: "<b>{label}</b>(<i>{{ bar_chart_items_percentage.1|safe }}%</i>)"  },
        { y: {{ bar_data_points.2|safe }},  label: "18-33", indexLabel: "{y}", indexLabelFontSize: '12', markerColor: "red", markerType: "triangle", toolTipContent: "<b>{label}</b>(<i>{{ bar_chart_items_percentage.2|safe }}%</i>)"  },
        { y: {{ bar_data_points.3|safe }},  label: "33-49", indexLabel: "{y}", indexLabelFontSize: '12', markerColor: "red", markerType: "triangle", toolTipContent: "<b>{label}</b>(<i>{{ bar_chart_items_percentage.3|safe }}%</i>)"  },
        { y: {{ bar_data_points.4|safe }},  label: "49-64", indexLabel: "{y}", indexLabelFontSize: '12', markerColor: "red", markerType: "triangle", toolTipContent: "<b>{label}</b>(<i>{{ bar_chart_items_percentage.4|safe }}%</i>)" },
        { y: {{ bar_data_points.5|safe }}, label: "64-80", indexLabel: "{y}", indexLabelFontSize: '12', markerColor: "red", markerType: "triangle", toolTipContent: "<b>{label}</b>(<i>{{ bar_chart_items_percentage.5|safe }}%</i>)"  },
        { y: {{ bar_data_points.6|safe }}, label: "80-95", indexLabel: "{y}", indexLabelFontSize: '12', markerColor: "red", markerType: "triangle", toolTipContent: "<b>{label}</b>(<i>{{ bar_chart_items_percentage.6|safe }}%</i>)"  },
        { y: {{ bar_data_points.7|safe }},  label: "Unknown", indexLabel: "{y}", indexLabelFontSize: '12', markerColor: "red", markerType: "triangle", toolTipContent: "<b>{label}</b>(<i>{{ bar_chart_items_percentage.7|safe }}%</i>)"  }
      ]
    }]
  });

  chart.render();

  }