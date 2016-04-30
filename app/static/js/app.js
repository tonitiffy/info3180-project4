var app = angular.module('wishlistApp', ['ngRoute', 'ui.bootstrap', 'ngAnimate'])

.run(function($rootScope, $location) {
    $rootScope.alerts = [];
})
.config(function($routeProvider){
    $routeProvider
    .when('/',{
        templateUrl:'static/partials/home.html'
    })
    .when('/login',{
        templateUrl: 'static/partials/login.html',
        controller: 'loginController'
    })
    .when('/logout',{
        templateUrl: 'static/partials/home.html',
        controller: 'logoutController'
    })
    .when('/signup',{
        templateUrl: 'static/partials/register.html',
        controller: 'registerController'
    })
    .when('/wishlist',{
        templateUrl: 'static/partials/wishlist.html',
        controller: 'wishlistController'
    })
    .when('/wishlist/add',{
        templateUrl: 'static/partials/addItem.html',
        controller: 'addController'
    })
    .when('/wishlist/share',{
        templateUrl: 'static/partials/share.html',
        controller: 'shareController'
    })
    .when('/user/:id/wishlist/shared_view',{
        templateUrl: 'static/partials/shared_view.html',
        controller: 'sharedViewController'
    })
    .otherwise({
       redirectTo: '/' 
    });
})
.controller('loginController', function ($scope, $location, $http, $rootScope){
    
    $scope.login = function () {
        
        $http({
        url: '/api/user/login',
        method: "POST",
        data: $.param({email: $scope.login.email, password: $scope.login.password}),
        headers: {'content-type': 'application/x-www-form-urlencoded'}
        })
        .then(function(response) {
            if (response['data']['error'] == null){
                localStorage.token = response['data']['data']['token'];
                $rootScope.userid = response['data']['data']['user']['_id'];
                $location.path('/wishlist');
            }
            else{
                $scope.alerts = [{ type: 'danger', msg: response['data']['message'] }];
                $scope.closeAlert = function(index) {$scope.alerts.splice(index, 1);};
                
            }
        });
    };
})
.controller('logoutController', function ($location, $rootScope){
    localStorage.removeItem('token');
    $rootScope.userid = null;
    $location.path('/login');
})
.controller('registerController', function ($scope, $http, $location, $rootScope) {
    
    $scope.register = function () {
        
        $http({
        url: '/api/user/register',
        method: "POST",
        data: $.param({name: $scope.reg.name, email: $scope.reg.email, password: $scope.reg.password}),
        headers: {'content-type': 'application/x-www-form-urlencoded'}
        })
        .then(function(response) {
            if (response['data']['error'] == null){
                localStorage.token = response['data']['data']['token'];
                $rootScope.userid = response['data']['data']['user']['_id'];
                $location.path('/wishlist');
            }
            else{
                $scope.alerts = [{ type: 'danger', msg: response['data']['message'] }];
                $scope.closeAlert = function(index) {$scope.alerts.splice(index, 1);};
            }
        });
        
    };
   
})
.controller('wishlistController', function ($scope, $http, $rootScope, $location) {
    
    if (localStorage.token != null){
        $http({
        url: '/api/user',
        method: "GET",
        headers: {'Authorization': 'Bearer '+ localStorage.token}
        })
        .then(function(response) {
            if (response['data']['error'] == null){
                
                $rootScope.userid = response['data']['data']['user']['_id'];
                var headers = {"Authorization": "Bearer " + localStorage.token};
                $http.get('/api/user/'+$rootScope.userid+'/wishlist', {headers:headers})
                .then(function(response){
                        $scope.items = response['data']['data']['wishes'];
                        $scope.alerts = $rootScope.alerts;
                        $scope.closeAlert = function(index) {$scope.alerts.splice(index, 1);};
                    });
            }
        }, function () {
            $location.path('/login');
        });
    }else{
        $location.path('/login');
    }
    
})
.controller('addController', function ($scope, $http, $routeParams, $rootScope, $location) {
    $rootScope.alerts = [];
    $scope.param = $routeParams.id;
    $scope.button = "Get Details";
    $scope.addButton = "Add Wish";
    
    $scope.getDetails = function () {
        $scope.button = "Getting the details...";
        $http.get('/api/thumbnail/process',{params:{"url": $scope.url}})
            .then(function(response) {
                
                if (response['data']['error'] == null){
                    $scope.alerts = [];
                    $scope.title = response['data']['data']['title'];
                    $scope.thumbnails = response['data']['data']['thumbnails'];
                    $scope.imgInstruct= "Select an image";
                    $scope.button = "Get Details";
                    $scope.thumbnail = $scope.thumbnails[0];
                    $scope.row = 0;
                }
                else{
                    $scope.alerts = [{ type: 'danger', msg: response['data']['message'] }];
                    $scope.closeAlert = function(index) {$scope.alerts.splice(index, 1);};
                    $scope.thumbnails = [];
                    $scope.title = "";
                    $scope.imgInstruct = "";
                    $scope.button = "Get Details";
                }
            });
   };
   $scope.getThumbnail = function (index) {
        $scope.thumbnail = $scope.thumbnails[index];
        $scope.row = index;
   };
    $scope.add = function () {
        $scope.addButton = "Adding your wish...";
        if (localStorage.token != null){
            $http({
            url: '/api/user',
            method: "GET",
            headers: {'Authorization': 'Bearer '+ localStorage.token}
            })
            .then(function(response) {
                if (response['data']['data']['error'] == null){
                    
                    $rootScope.userid = response['data']['data']['user']['_id'];
                    $http({
                    url: '/api/user/'+$rootScope.userid+'/wishlist',
                    method: "POST",
                    data: $.param({title: $scope.title, description: $scope.descript, url: $scope.url, thumbnail: $scope.thumbnail}),
                    headers: {'content-type': 'application/x-www-form-urlencoded', 'Authorization': 'Bearer ' + localStorage.token}
                    })
                    .then(function(response) {
                        
                        if (response['data']['error'] == null){
                            $location.path('/wishlist');
                            $rootScope.alerts = [{ type: 'success', msg: response['data']['message'] }];
                        }
                        else{
                            $scope.alerts = [{ type: 'danger', msg: response['data']['message'] }];
                            $scope.closeAlert = function(index) {$scope.alerts.splice(index, 1);};
                            $scope.addButton = "Add Wish";
                        }
                    });
                }
            }, function () {
                $location.path('/login');
            });
        }
    };
   
})
.controller('shareController', function ($scope, $http, $routeParams, $location, $rootScope) {
    $rootScope.alerts = [];
    $scope.param = $routeParams.id;
    
    $scope.share = function () {
        
        if (localStorage.token != null){
            $http({
            url: '/api/user',
            method: "GET",
            headers: {'Authorization': 'Bearer '+ localStorage.token}
            })
            .then(function(response) {
                if (response['data']['error'] == null){
                    
                    $rootScope.userid = response['data']['data']['user']['_id'];
                    $http({
                    url: '/api/user/'+$rootScope.userid+'/wishlist/share',
                    method: "POST",
                    data: $.param({email1: $scope.email1, email2: $scope.email2, email3: $scope.email3, email4: $scope.email4, email5: $scope.email5}),
                    headers: {'content-type': 'application/x-www-form-urlencoded', 'Authorization': 'Bearer ' + localStorage.token}
                    })
                    .then(function(response) {
                        $location.path('/wishlist');
                        $rootScope.alerts = [{ type: 'success', msg: response['data']['message'] }];
                    });
                }
            }, function () {
                $location.path('/login');
            });
        }
    };
})
.controller('sharedViewController', function ($scope, $http, $routeParams, $location) {
    
    $http.get('/api/user/'+$routeParams.id+'/wishlist/shared')
    .then(function(response){
        if (response['data']['data']['errors'] == null){
            $scope.items = response['data']['data']['wishes'];
            $scope.name = response['data']['data']['user']['name'];
        }else{
            $location.path('/');    
        }
        });
});