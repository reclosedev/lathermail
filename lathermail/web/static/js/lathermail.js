var lathermailApp = angular.module('lathermailApp', ['ngRoute', 'angularMoment', 'ngStorage'])


.config(['$routeProvider', '$locationProvider',
  function($routeProvider) {
    $routeProvider.
      when('/messages', {
        controller: 'lathermailCtrl'
      }).
      when('/messages/:messageId', {
        redirectTo: function (params) {
          return '/messages/' + params.messageId + '/text'
        }
      }).
      when('/messages/:messageId/:currentTab', {
        templateUrl: function (params) {
          return 'message.' + params.currentTab + '.html'
        },
        controller: 'lathermailDetailCtrl'
      }).
      otherwise({
        redirectTo: '/messages'
      });
}]);


lathermailApp.controller('lathermailCtrl', function ($scope, $http, $routeParams, $location, $localStorage) {
  $scope.$storage = $localStorage.$default({
    inbox: null,
    password: "password"
  });
  $scope.query = "";
  $scope.params = $routeParams;
  $scope.inboxes = [];
  $scope.tabs = [
    {url: "text", title: function(){return "Text"}},
    {url: "html", title: function(){return "HTML"}},
    {url: "raw", title: function(){return "Raw"}},
    {
      url: "attachments",
      title: function(message){
        var attachmentCount = 0;
        if(message){
          message.parts.forEach(function(p){
            if(p.is_attachment) attachmentCount++;
          });
          message.attachmentCount = attachmentCount;
        }
        return "Attachments" + "(" + attachmentCount + ")";
      }
    }
  ];

  $scope.messageById  = {};
  $scope.messages = null;
  $scope.selectedMessage = null;

  $scope.refreshMessages = function () {
    $http.defaults.headers.common = {
      "X-Mail-Inbox": $scope.$storage.inbox,
      "X-Mail-Password": $scope.$storage.password
    };

    return $http.get("/api/0/inboxes/").then(function(resp) {
      $scope.inboxes = resp.data.inbox_list;
      if ($scope.inboxes.length && (!$scope.$storage.inbox || $scope.inboxes.indexOf($scope.$storage.inbox) == -1)) {
        $scope.$storage.inbox = $scope.inboxes[0];
      }
      $http.defaults.headers.common["X-Mail-Inbox"] = $scope.$storage.inbox;
    }).then(function () {
      return $http.get("/api/0/messages/").then(function (resp) {
        $scope.messages = resp.data.message_list;
        $scope.messageById  = {};

        var index = 0;
        $scope.messages.forEach(function(message){
          message.index = index++;
          $scope.messageById[message._id] = message;
        });

        if ($routeParams.messageId) {
          $scope.selectMessage($scope.messageById[$routeParams.messageId]);
        } else {
          $location.path("/messages/" + $scope.messages[0]._id)
        }
        if (!$scope.messages || !$scope.messages.length){
          $scope.selectedMessage = null;
        }
      });
    });
  };

  $scope.selectMessage = function (message) {
    $scope.selectedMessage = message;
  };

  $scope.isActiveMessage = function(message){
    return $scope.selectedMessage  && message._id === $scope.selectedMessage._id;
  };

  $scope.deleteMessage = function () {
    $http.delete("/api/0/messages/" + $scope.selectedMessage._id).then(function (resp) {
      var index = $scope.selectedMessage.index;

      $scope.refreshMessages().then(function () {
        index = Math.max(Math.min(index, $scope.messages.length), 0);
        if($scope.messages.length > 1){
          $scope.go('/messages/' + $scope.messages[index]._id + '/' + $routeParams.currentTab);
        }
      });
    });
  };

  $scope.deleteAllMessages = function () {
    if(confirm("Are you sure you wan't to delete all messages in '" + $scope.$storage.inbox + "'?")){
      $http.delete("/api/0/messages/").then(function (resp) {
        $scope.refreshMessages();
      });
    }
  };

  $scope.isActiveTab = function (tabUrl) {
    return tabUrl === $routeParams.currentTab;
  };
  $scope.go = function(path){
    $location.path(path);
  };

  $scope.refreshMessages();
})
.controller('lathermailDetailCtrl', function ($scope, $http, $routeParams) {
  $scope.params = $routeParams;

  if ($routeParams.messageId && $scope.messageById){
    var message = $scope.messageById[$routeParams.messageId];
    if (message){
      $scope.selectMessage(message);
    }
  }
})

.filter("trust", ['$sce', function($sce) {
  return function(htmlCode){
    return $sce.trustAsHtml(htmlCode);
  }
}])

.directive("recipients", function(){
  return {
    restrict: "E",
    replace: true,
    scope: {
        recipients: '='
    },
    template: '<span ng-repeat="rcpt in recipients">{{ rcpt.name }} &lt;{{ rcpt.address }}&gt;{{$last ? "" : ", "}}</span>'
  }
})
.directive('fullHeight', function ($window) {
  return {
    restrict: 'A',
    link: function (scope, element, attrs) {
      var handle = function(){
        element.css({'height': $window.innerHeight - element.offset().top});
      };
      angular.element($window).bind('resize', handle);
      scope.$watch(handle);
    }
  };
});
