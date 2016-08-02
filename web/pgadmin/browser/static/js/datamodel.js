define(
   ['underscore', 'pgadmin', 'jquery', 'backbone'],
function(_, pgAdmin, $, Backbone) {
  var pgBrowser = pgAdmin.Browser = pgAdmin.Browser || {};

  pgBrowser.DataModel = Backbone.Model.extend({
      /*
       * Parsing the existing data
       */
      parse: function(res) {
        var self = this;
        if (res && _.isObject(res) && 'node' in res && res['node']) {
          self.tnode = _.extend({}, res.node);
          delete res.node;
        }
        var objectOp = function(schema) {
          if (schema && _.isArray(schema)) {
            _.each(schema, function(s) {
              var obj, val;
              switch(s.type) {
                case 'collection':
                  obj = self.get(s.id);
                  val = res[s.id];
                  if (_.isArray(val) || _.isObject(val)) {
                    if (!obj || !(obj instanceof Backbone.Collection)) {
                      obj = new (pgBrowser.Node.Collection)(val, {
                        model: ((_.isString(s.model) &&
                                 s.model in pgBrowser.Nodes) ?
                                pgBrowser.Nodes[s.model].model : s.model),
                        top: self.top || self,
                        handler: self,
                        parse: true,
                        silent: true,
                        attrName: s.id
                        });
                      self.set(s.id, obj, {silent: true, parse: true});
                    } else {
                      obj.reset(val, {silent: true, parse: true});
                    }
                  }
                  else {
                    if (obj)
                      delete obj;
                    obj = null;
                  }
                  self.set(s.id, obj, {silent: true});
                  res[s.id] = obj;
                  break;
                case 'model':
                  obj = self.get(s.id);
                  val = res[s.id];
                  if (!_.isUndefined(val) && !_.isNull(val)) {
                    if (!obj || !(obj instanceof Backbone.Model)) {
                      if (_.isString(s.model) &&
                          s.model in pgBrowser.Nodes[s.model]) {
                        obj = new (pgBrowser.Nodes[s.model].Model)(
                            obj, {
                              silent: true, top: self.top || self, handler: self,
                              attrName: s.id
                            }
                            );
                      } else {
                        obj = new (s.model)(obj, {
                          silent: true, top: self.top || self, handler: self,
                          attrName: s.id
                        });
                      }
                    }
                    obj.set(val, {parse: true, silent: true});
                  } else {
                    if (obj)
                      delete obj;
                    obj = null;
                  }
                  res[s.id] = obj;
                  break;
                case 'nested':
                  objectOp(s.schema);

                  break;
                default:
                  break;
              }
            });
          }
        };

        objectOp(self.schema);

        return res;
      },
      primary_key: function() {
        if (this.keys && _.isArray(this.keys)) {
          var res = {}, self = this;

          _.each(self.keys, function(k) {
            res[k] = self.attributes[k];
          });

          return JSON.stringify(res);
        }
        return this.cid;
      },
      initialize: function(attributes, options) {
        var self = this;

        Backbone.Model.prototype.initialize.apply(self, arguments);

        if (_.isUndefined(options) || _.isNull(options)) {
          options = attributes || {};
          attributes = null;
        }

        self.sessAttrs = {};
        self.origSessAttrs = {};
        self.objects = [];
        self.arrays = [];
        self.attrName = options.attrName,
        self.top = (options.top || self.collection && self.collection.top || self.collection || self);
        self.handler = options.handler ||
          (self.collection && self.collection.handler);
        self.trackChanges = false;
        self.errorModel = new Backbone.Model();
        self.node_info = options.node_info;

        var obj;
        var objectOp = function(schema) {
          if (schema && _.isArray(schema)) {
            _.each(schema, function(s) {

              switch(s.type) {
                case 'array':
                  self.arrays.push(s.id);

                  break;
                case 'collection':
                  obj = self.get(s.id)
                  if (!obj || !(obj instanceof pgBrowser.Node.Collection)) {
                    if (_.isString(s.model) &&
                      s.model in pgBrowser.Nodes) {
                      var node = pgBrowser.Nodes[s.model];
                      obj = new (node.Collection)(obj, {
                        model: node.model,
                        top: self.top || self,
                        handler: self,
                        attrName: s.id
                      });
                    } else {
                      obj = new (pgBrowser.Node.Collection)(obj, {
                        model: s.model,
                        top: self.top || self,
                        handler: self,
                        attrName: s.id
                      });
                    }
                  }

                  obj.name = s.id;
                  self.objects.push(s.id);
                  self.set(s.id, obj, {silent: true});

                  break;
                case 'model':
                  obj = self.get(s.id)
                  if (!obj || !(obj instanceof Backbone.Model)) {
                    if (_.isString(s.model) &&
                        s.model in pgBrowser.Nodes[s.model]) {
                      obj = new (pgBrowser.Nodes[s.model].Model)(
                          obj, {
                            top: self.top || self, handler: self, attrName: s.id
                          }
                          );
                    } else {
                      obj = new (s.model)(
                          obj, {
                            top: self.top || self, handler: self, attrName: s.id
                          });
                    }
                  }

                  obj.name = s.id;
                  self.objects.push(s.id);
                  self.set(s.id, obj, {silent: true});

                  break;
                case 'nested':
                  objectOp(s.schema);
                  break;
                default:
                  return;
              }
            });
          }
        };
        objectOp(self.schema);

        if (self.handler && self.handler.trackChanges) {
          self.startNewSession();
        }

        return self;
      },
      // Create a reset function, which allow us to remove the nested object.
      reset: function(opts) {
        var obj;

        if (opts && opts.stop)
            this.stopSession();

        for(id in this.objects) {
          obj = this.get(id);

          if (obj) {
            if (obj instanceof pgBrowser.DataModel) {
              obj.reset(opts);
              delete obj;
            } else if (obj instanceof Backbone.Model) {
              obj.clear(opts);
              delete obj;
            } else if (obj instanceof pgBrowser.DataCollection) {
              obj.reset(opts);
              delete obj;
            } else if (obj instanceof Backbone.Collection) {
              obj.each(function(m) {
                if (m instanceof Backbone.DataModel) {
                  obj.reset();
                  obj.clear(opts);
                }
              });
              if (!(opts instanceof Array)){ opts = [opts] }
              Backbone.Collection.prototype.reset.apply(obj, opts);
              delete obj;
            }
          }
        }
        this.clear(opts);
      },
      sessChanged: function() {
        var self = this;

        return (_.size(self.sessAttrs) > 0 ||
            _.some(self.objects, function(k) {
              var obj = self.get(k);
              if (!(_.isNull(obj) || _.isUndefined(obj))) {
                return obj.sessChanged();
              }
              return false;
            }));
      },
      sessValid: function() {
        var self = this;
        if ('validate' in self && _.isFunction(self.validate) &&
            _.isString(self.validate.apply(self))) {
          return false;
        }
        return true;
      },
      set: function(key, val, options) {
        var opts = _.isObject(key) ? val : options;

        this._changing = true;
        this._previousAttributes = _.clone(this.attributes);
        this.changed = {};

        var res = Backbone.Model.prototype.set.call(this, key, val, options);
        this._changing = false;

        if ((opts&& opts.internal) || !this.trackChanges) {
          return true;
        }

        if (key != null && res) {
          var attrs = {};
          var self = this;

          attrChanged = function(v, k) {
            if (k in self.objects) {
              return;
            }
            attrs[k] = v;
            if (_.isEqual(self.origSessAttrs[k], v)) {
              delete self.sessAttrs[k];
            } else {
              self.sessAttrs[k] = v;
            }
          };

          // Handle both `"key", value` and `{key: value}` -style arguments.
          if (typeof key === 'object') {
            _.each(key, attrChanged);
          } else {
            attrChanged(val, key);
          }

          self.trigger('pgadmin-session:set', self, attrs);
          if (!options || !options.silent) {
            self.trigger('change', self, options);
          }
          if ('validate' in self && typeof(self['validate']) === 'function') {

            var msg = self.validate(_.keys(attrs));

            /*
             * If any parent present, we will need to inform the parent - that
             * I have some issues/fixed the issue.
             *
             * If not parent found, we will raise the issue
             */
            if (_.size(self.errorModel.attributes) == 0) {
              if (self.collection || self.handler) {
                (self.collection || self.handler).trigger(
                    'pgadmin-session:model:valid', self, (self.collection || self.handler)
                    );
              } else {
                self.trigger('pgadmin-session:valid', self.sessChanged(), self);
              }
            } else {
              msg = msg || _.values(self.errorModel.attributes)[0];
              if (self.collection || self.handler) {
                (self.collection || self.handler).trigger(
                    'pgadmin-session:model:invalid', msg, self, (self.collection || self.handler)
                    );
              } else {
                self.trigger('pgadmin-session:invalid', msg, self);
              }
            }
          }

          return res;
        }
        return res;
      },
      /*
       * We do support modified data only through session by tracking changes.
       *
       * In normal mode, we will use the toJSON function of Backbone.Model.
       * In session mode, we will return all the modified data only. And, the
       * objects (collection, and model) will be return as stringified JSON,
       * only from the parent object.
       */
      toJSON: function(session, method) {
        var self = this, res, isNew = self.isNew();

        session = (typeof(session) != "undefined" && session == true);

        if (!session || isNew) {
          res = Backbone.Model.prototype.toJSON.call(this, arguments);
        } else {
          res = {};
          res[self.idAttribute || '_id'] = self.get(self.idAttribute || '_id');
          res = _.extend(res, self.sessAttrs);
        }

        /*
         * We do have number objects (models, collections), which needs to be
         * converted to JSON data manually.
         */
        _.each(
            self.objects,
            function(k) {
              var obj = self.get(k);
              /*
               * For session changes, we only need the modified data to be
               * transformed to JSON data.
               */
              if (session) {
                if (res[k] instanceof Array) {
                  res[k] = JSON.stringify(res[k]);
                } else if ((obj && obj.sessChanged && obj.sessChanged()) || isNew) {
                  res[k] = obj && obj.toJSON(!isNew);
                  /*
                   * We will run JSON.stringify(..) only from the main object,
                   * not for the JSON object within the objects, that only when
                   * HTTP method is 'GET'.
                   *
                   * We do stringify the object, so that - it will not be
                   * translated to wierd format using jQuery.
                   */
                  if (obj && method && method == 'GET') {
                    res[k] = JSON.stringify(res[k]);
                  }
                } else {
                  delete res[k];
                }
              } else if (!(res[k] instanceof Array)) {
                res[k] = (obj && obj.toJSON());
              }
            });
        if (session) {
          _.each(
              self.arrays,
              function(a) {
                /*
                 * For session changes, we only need the modified data to be
                 * transformed to JSON data.
                 */
                if (res[a] && res[a] instanceof Array) {
                  res[a] = JSON.stringify(res[a]);
                }
              });
        }
        return res;
      },
      startNewSession: function() {
        var self = this;

        if (self.trackChanges) {
          self.trigger('pgadmin-session:stop', self);
          self.off('pgadmin-session:model:invalid', self.onChildInvalid);
          self.off('pgadmin-session:model:valid', self.onChildValid);
          self.off('pgadmin-session:changed', self.onChildChanged);
          self.off('pgadmin-session:added', self.onChildChanged);
          self.off('pgadmin-session:removed', self.onChildChanged);
        }

        self.trackChanges = true;
        self.sessAttrs = {};
        self.origSessAttrs = _.clone(self.attributes);

        var res = false;

        _.each(self.objects, function(o) {
          var obj = self.get(o);

          if (_.isUndefined(obj) || _.isNull(obj)) {
            return;
          }

          delete self.origSessAttrs[o];

          if (obj && 'startNewSession' in obj && _.isFunction(obj.startNewSession)) {
            obj.startNewSession();
          }
        });

        // Let people know, I have started session hanlding
        self.trigger('pgadmin-session:start', self);

        // Let me listen to the my child invalid/valid messages
        self.on('pgadmin-session:model:invalid', self.onChildInvalid);
        self.on('pgadmin-session:model:valid', self.onChildValid);
        self.on('pgadmin-session:changed', self.onChildChanged);
        self.on('pgadmin-session:added', self.onChildChanged);
        self.on('pgadmin-session:removed', self.onChildChanged);
      },

      onChildInvalid: function(msg, obj) {
        var self = this;

        if (self.trackChanges && obj) {
          var objName = obj.attrName;

          if (!objName) {
            var hasPrimaryKey = obj.primary_key &&
                  typeof(obj.primary_key) === 'function';
                key = hasPrimaryKey ? obj.primary_key() : obj.cid,
                comparator = hasPrimaryKey ?
                  function(k) {
                    var o = self.get('k');

                    if (o && o.primary_key() === key) {
                      objName = k;
                      return true;
                    }

                    return false;
                  } :
                  function(k) {
                    var o = self.get(k);

                    if (o.cid === key) {
                      objName = k;
                      return true;
                    }

                    return false;
                  };
            _.findIndex(self.objects, comparator);
          }

          if (objName) {
            /*
             * Update the error message for this object.
             */
            self.errorModel.set(objName, msg);

            if (self.handler) {
              (self.handler).trigger('pgadmin-session:model:invalid', msg, self, self.handler);
            } else  {
              self.trigger('pgadmin-session:invalid', msg, self);
            }
          }
        }

        return this;
      },
      onChildValid: function(obj) {
        var self = this;

        if (self.trackChanges && obj) {
          var objName = obj.attrName;

          if (!objName) {
              var hasPrimaryKey = (obj.primary_key &&
                (typeof(obj.primary_key) === 'function'));
              key = hasPrimaryKey ? obj.primary_key() : obj.cid,
              comparator = hasPrimaryKey ?
                function(k) {
                  var o = self.get('k');

                  if (o && o.primary_key() === key) {
                    objName = k;
                    return true;
                  }

                  return false;
                } :
                function(k) {
                  var o = self.get('k');

                  if (o && o.cid === key) {
                    objName = k;
                    return true;
                  }

                  return false;
                };

              _.findIndex(self.objects, comparator);
          }

          var msg = null,
              validate = function(m, attrs) {
                if ('validate' in m && typeof(m.validate) == 'function') {
                  msg = m.validate(attrs);

                  return msg;
                }
                return null;
              };

          if (obj instanceof Backbone.Collection) {
            for (idx in obj.models) {
              if (validate(obj.models[idx]))
                break;
            }
          } else if (obj instanceof Backbone.Model) {
            validate(obj);
          }

          if (objName && self.errorModel.has(objName)) {
            if (!msg) {
              self.errorModel.unset(objName);
            } else {
              self.errorModel.set(objName, msg);
            }
          }

          /*
           * The object is valid, but does this has any effect on parent?
           * Let's validate this object itself, before making it clear.
           *
           * We will trigger validation information.
           */
          if (_.size(self.errorModel.attributes) == 0 &&
              !validate(self, (objName && [objName]))) {
            if (self.handler) {
              (self.handler).trigger('pgadmin-session:model:valid', self, self.handler);
            } else  {
              self.trigger(
                  'pgadmin-session:valid', self.sessChanged(), self
                  );
            }
          } else {
            msg = msg || _.values(self.errorModel.attributes)[0];

            if (self.handler) {
              (self.handler).trigger(
                  'pgadmin-session:model:invalid', msg, self, self.handler
                  );
            } else  {
              self.trigger('pgadmin-session:invalid', msg, self);
            }
          }
        }
      },

      onChildChanged: function(obj) {
        var self = this;

        if (self.trackChanges && self.collection) {
          (self.collection).trigger('change', self);
        }
      },

      stopSession: function() {
        var self = this;

        if (self.trackChanges) {
          self.off('pgadmin-session:model:invalid', self.onChildInvalid);
          self.off('pgadmin-session:model:valid', self.onChildValid);
          self.off('pgadmin-session:changed', self.onChildChanged);
          self.off('pgadmin-session:added', self.onChildChanged);
          self.off('pgadmin-session:removed', self.onChildChanged);
        }

        self.trackChanges = false;
        self.sessAttrs = {};
        self.origSessAttrs = {};

        _.each(self.objects, function(o) {
          var obj = self.get(o);

          if (_.isUndefined(obj) || _.isNull(obj)) {
            return;
          }

          self.origSessAttrs[o] = null;
          delete self.origSessAttrs[o];

          if (obj && 'stopSession' in obj && _.isFunction(obj.stopSession)) {
            obj.stopSession();
          }
        });

        self.trigger('pgadmin-session:stop');
      }
    });

    pgBrowser.DataCollection = Backbone.Collection.extend({
      // Model collection
      initialize: function(attributes, options) {
        var self = this;

        options = options || {};
        /*
         * Session changes will be kept in this object.
         */
        self.sessAttrs = {
          'changed': [],
          'added': [],
          'deleted': [],
          'invalid': []
        };
        self.top = options.top || self;
        self.attrName = options.attrName;
        self.handler = options.handler;
        self.trackChanges = false;

        /*
         * Listen to the model changes for the session changes.
         */
        self.on('add', self.onModelAdd);
        self.on('remove', self.onModelRemove);
        self.on('change', self.onModelChange);

        /*
         * We need to start the session, if the handler is already in session
         * tracking mode.
         */
        if (self.handler && self.handler.trackChanges) {
          self.startNewSession();
        }

        return self;
      },
      startNewSession: function() {
        var self = this;

        if (self.trackChanges) {
          // We're stopping the existing session.
          self.trigger('pgadmin-session:stop', self);

          self.off('pgadmin-session:model:invalid', self.onModelInvalid);
          self.off('pgadmin-session:model:valid', self.onModelValid);
        }

        self.trackChanges = true;
        self.sessAttrs = {
          'changed': [],
          'added': [],
          'deleted': [],
          'invalid': []
        };

        _.each(self.models, function(m) {
          if ('startNewSession' in m && _.isFunction(m.startNewSession)) {
            m.startNewSession();
          }
          if ('validate' in m && typeof(m.validate) === 'function') {
            var msg = m.validate();

            if (msg) {
              self.sessAttrs['invalid'][m.cid] = msg;
            }
          }
        });

        // Let people know, I have started session hanlding
        self.trigger('pgadmin-session:start', self);

        self.on('pgadmin-session:model:invalid', self.onModelInvalid);
        self.on('pgadmin-session:model:valid', self.onModelValid);
      },
      onModelInvalid: function(msg, m) {
        var self = this,
            invalidModels = self.sessAttrs['invalid'];

        if (self.trackChanges) {
          // Do not add the existing invalid object
          invalidModels[m.cid] = msg;

          // Inform the parent that - I am an invalid model.
          if (self.handler) {
            (self.handler).trigger('pgadmin-session:model:invalid', msg, self, self.handler);
          } else {
            self.trigger('pgadmin-session:invalid', msg, self);
          }
        }

        return true;
      },
      onModelValid: function(m) {
        var self = this,
            invalidModels = self.sessAttrs['invalid'];

        if (self.trackChanges) {
          // Find the object the invalid list, if found remove it from the list
          // and inform the parent that - I am a valid object now.
          if (m.cid in invalidModels) {
            delete invalidModels[m.cid];
          }

          this.triggerValidationEvent.apply(this);
        }

        return true;
      },
      stopSession: function() {
        var self = this;

        self.trackChanges = false;
        self.sessAttrs = {
          'changed': [],
          'added': [],
          'deleted': [],
          'invalid': []
        };

        _.each(self.models, function(m) {
          if ('stopSession' in m && _.isFunction(m.stopSession)) {
            m.stopSession();
          }
        });
      },
      sessChanged: function() {
        return (
            this.sessAttrs['changed'].length > 0 ||
            this.sessAttrs['added'].length > 0 ||
            this.sessAttrs['deleted'].length > 0
            );
      },
      /*
       * We do support the changes through session tracking in general.
       *
       * In normal mode, we will use the general toJSON(..) function of
       * Backbone.Colletion.
       *
       * In session mode, we will return session changes as:
       * We will be returning the session changes as:
       * {
       *  'added': [JSON of each new model],
       *  'delete': [JSON of each deleted model],
       *  'changed': [JSON of each modified model with session changes]
       * }
       */
      toJSON: function(session) {
        var self = this,
            session = (typeof(session) != "undefined" && session == true);

        if (!session) {
          return Backbone.Collection.prototype.toJSON.call(self);
        } else {
          var res = {};

          res['added'] = [];
          _.each(this.sessAttrs['added'], function(o) {
            res['added'].push(o.toJSON());
          });
          if (res['added'].length == 0) {
            delete res['added'];
          }
          res['changed'] = [];
          _.each(self.sessAttrs['changed'], function(o) {
            res['changed'].push(o.toJSON(true));
          });
          if (res['changed'].length == 0) {
            delete res['changed'];
          }
          res['deleted'] = [];
          _.each(self.sessAttrs['deleted'], function(o) {
            res['deleted'].push(o.toJSON());
          });
          if (res['deleted'].length == 0) {
            delete res['deleted'];
          }

          return (_.size(res) == 0 ? null : res);
        }
      },
      // Override the reset function, so that - we can reset the model
      // properly.
      reset: function(opts) {
        if (opts && opts.stop)
            this.stopSession();
        this.each(function(m) {
          if (!m)
            return;
          if (m instanceof pgBrowser.DataModel) {
            m.reset(opts);
          } else {
            m.clear(opts);
          }
        });
        Backbone.Collection.prototype.reset.apply(this, arguments);
      },
      objFindInSession: function(m, type) {
        var hasPrimaryKey = m.primary_key &&
              typeof(m.primary_key) == 'function',
            key = hasPrimaryKey ? m.primary_key() : m.cid,
            comparator = hasPrimaryKey ? function(o) {
              return (o.primary_key() === key);
            } : function(o) {
              return (o.cid === key);
            };

        return (_.findIndex(this.sessAttrs[type], comparator));
      },
      onModelAdd: function(obj) {

        if (!this.trackChanges)
          return true;

        var self = this,
            msg,
            isAlreadyInvalid = (_.size(self.sessAttrs['invalid']) != 0),
            idx = self.objFindInSession(obj, 'deleted');

        // Hmm.. - it was originally deleted from this collection, we should
        // remove it from the 'deleted' list.
        if (idx >= 0) {
          var origObj = self.sessAttrs['deleted'][idx];

          obj.origSessAttrs = _.clone(origObj.origSessAttrs);
          obj.attributes = _.extend(obj.attributes, origObj.attributes);
          obj.sessAttrs = _.clone(origObj.sessAttrs);

          self.sessAttrs['deleted'].splice(idx, 1);

          // It has been changed originally!
          if ((!'sessChanged' in obj) || obj.sessChanged()) {
            self.sessAttrs['changed'].push(obj);
          }

          (self.handler || self).trigger('pgadmin-session:added', self, obj);

          if ('validate' in obj && typeof(obj.validate) === 'function') {
            msg = obj.validate();

            if (msg) {
              (self.sessAttrs['invalid'])[obj.cid] = msg;
            }
          }

          // Let the parent/listener know about my status (valid/invalid).
          this.triggerValidationEvent.apply(this);

          return true;
        }
        if ('validate' in obj && typeof(obj.validate) === 'function') {
          msg = obj.validate();

          if (msg) {
            (self.sessAttrs['invalid'])[obj.cid] = msg;
          }
        }
        self.sessAttrs['added'].push(obj);

        /*
         * Session has been changed
         */
        (self.handler || self).trigger('pgadmin-session:added', self, obj);

        // Let the parent/listener know about my status (valid/invalid).
        this.triggerValidationEvent.apply(this);

        return true;
      },
      onModelRemove: function(obj) {

        if (!this.trackChanges)
          return true;

        var self = this,
            invalidModels = self.sessAttrs['invalid'],
            copy = _.clone(obj),
            idx = self.objFindInSession(obj, 'added');

        // We need to remove it from the invalid object list first.
        if (obj.cid in invalidModels) {
          delete invalidModels[obj.cid];
        }

        // Hmm - it was newly added, we can safely remove it.
        if (idx >= 0) {
          self.sessAttrs['added'].splice(idx, 1);

          (self.handler || self).trigger('pgadmin-session:removed', self, copy);

          // Let the parent/listener know about my status (valid/invalid).
          this.triggerValidationEvent.apply(this);

          return true;
        }

        // Hmm - it was changed in this session, we should remove it from the
        // changed models.
        idx = self.objFindInSession(obj, 'changed');

        if (idx >= 0) {
          self.sessAttrs['changed'].splice(idx, 1);
          (self.handler || self).trigger('pgadmin-session:removed', self, copy);
        } else {
          (self.handler || self).trigger('pgadmin-session:removed', self, copy);
        }

        self.sessAttrs['deleted'].push(obj);

        // Let the parent/listener know about my status (valid/invalid).
        this.triggerValidationEvent.apply(this);

        /*
         * This object has been remove, we need to check (if we still have any
         * other invalid message pending).
         */

        return true;
      },
      triggerValidationEvent: function() {
        var self = this,
            msg = null,
            invalidModels = self.sessAttrs['invalid'],
            validModels = [];

        for (var key in invalidModels) {
          msg = invalidModels[key];
          if (msg) {
            break;
          }
          else {
            // Hmm..
            // How come - you have been assinged in invalid list.
            // I will make a list of it, and remove it later.
            validModels.push(key);
          }
        }

        // Let's remove the un
        for (key in validModels) {
          delete invalidModels[validModels[key]];
        }

        if (!msg) {
          if (self.handler) {
            self.handler.trigger('pgadmin-session:model:valid', self, self.handler);
          } else {
            self.trigger('pgadmin-session:valid', self.sessChanged(), self);
          }
        } else {
          if (self.handler) {
            self.handler.trigger('pgadmin-session:model:invalid', msg, self, self.handler);
          } else {
            self.trigger('pgadmin-session:invalid', msg, self);
          }
        }
      },
      onModelChange: function(obj) {

        if (!this.trackChanges || !(obj instanceof pgBrowser.Node.Model))
          return true;

        var self = this,
            idx = self.objFindInSession(obj, 'added');

        // It was newly added model, we don't need to add into the changed
        // list.
        if (idx >= 0) {
          (self.handler || self).trigger('pgadmin-session:changed', self, obj);

          return true;
        }

        idx = self.objFindInSession(obj, 'changed');

        if (!'sessChanged' in obj) {
          (self.handler || self).trigger('pgadmin-session:changed', self, obj);

          if (idx >= 0) {
            return true;
          }

          self.sessAttrs['changed'].push(obj);

          return true;
        }

        if (idx >= 0) {

          if (!obj.sessChanged()) {
            // This object is no more updated, removing it from the changed
            // models list.
            self.sessAttrs['changed'].splice(idx, 1);

            (self.handler || self).trigger('pgadmin-session:changed',self, obj);
            return true;
          }

          (self.handler || self).trigger('pgadmin-session:changed',self, obj);

          return true;
        }

        self.sessAttrs['changed'].push(obj);
        (self.handler || self).trigger('pgadmin-session:changed', self, obj);

        return true;
      }
    });

    pgBrowser.Events = _.extend({}, Backbone.Events);

    return pgBrowser;
});
