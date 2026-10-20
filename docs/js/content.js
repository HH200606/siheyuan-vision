/* =============================================================================
   四合檐影 · 内容层
   五类构件、每类四个形制，以及关卡与评分规则。
   ========================================================================== */

const CATEGORIES = {
  window: {
    title: '窗棂',
    lead: '木窗的棂条拼出的纹样，是四合院里最见巧思的地方。',
    variants: {
      bubujin: {
        name: '步步锦',
        note: '横竖棂条搭成阶梯状锦纹，取「步步高升」的彩头，是宅院里最常见的窗心。',
      },
      binglie: {
        name: '冰裂纹',
        note: '棂条像冰面裂开的纹，不规整却匀称，多用在书房与园林，取「冰清玉洁」。',
      },
      guibei: {
        name: '龟背锦',
        note: '六边形连缀如龟甲，寓意长寿稳固，做工比步步锦费料。',
      },
      denglong: {
        name: '灯笼框',
        note: '窗心做成灯笼形，四周留白，年节糊上红纸，取「光明」之意。',
      },
    },
  },

  doorstone: {
    title: '门墩',
    lead: '门枕石露在门外的那一半，是门第等级最直白的说明书。',
    variants: {
      shizi: {
        name: '狮子门墩',
        note: '门枕石上雕狮子，多用于武官宅第。狮子镇宅辟邪，也显主人身份。',
      },
      baogu: {
        name: '抱鼓石',
        note: '形如圆鼓，鼓面雕纹，两侧有卷草。俗话说「门前抱鼓，非富即贵」。',
      },
      xiangxing: {
        name: '箱形门墩',
        note: '方形如箱，面上多雕书卷、如意，读书人家与文官宅第常见。',
      },
      xumizuo: {
        name: '须弥座门墩',
        note: '用须弥座的层叠线脚做墩身，等级较高，只有大宅才用得起。',
      },
    },
  },

  brick: {
    title: '砖雕',
    lead: '青砖上剔出来的浅浮雕，是四合院的「软装」，题材都有说法。',
    variants: {
      huacao: {
        name: '花草砖雕',
        note: '牡丹、菊花、卷草为主，取富贵、长寿。最常见于影壁与墀头。',
      },
      bogu: {
        name: '博古砖雕',
        note: '瓶、书、鼎、如意等器物组合，「瓶」谐音「平」，取平安如意。',
      },
      ruishou: {
        name: '瑞兽砖雕',
        note: '麒麟、狮子、鹿等瑞兽，辟邪纳吉，多用在门楣与影壁中心。',
      },
      huiwen: {
        name: '回纹砖雕',
        note: '连续的回字纹，绵延不断，取「富贵不断头」，常做边框。',
      },
    },
  },

  gate: {
    title: '院门',
    lead: '门开多大、门扇装多深，直接对应主人的身份。',
    variants: {
      guangliang: {
        name: '广亮大门',
        note: '门扇装在门道中柱位置，门道深、门框宽，等级最高，多为官员宅第。',
      },
      jinzhu: {
        name: '金柱大门',
        note: '门扇装在前檐金柱，门道比广亮大门浅，等级次之。',
      },
      ruyi: {
        name: '如意门',
        note: '门洞较窄，门楣上常用砖雕如意纹，多为一般富户。',
      },
      suqiang: {
        name: '随墙门',
        note: '直接在院墙上开门洞，没有独立门楼，朴素，小户人家常见。',
      },
    },
  },

  eave: {
    title: '檐部',
    lead: '屋檐上最容易被忽略的几个小件，恰恰是古建的「关节」。',
    variants: {
      feiyan: {
        name: '飞檐翘角',
        note: '屋檐转角向上翘起如鸟翼，既把雨水甩远，也让沉重的屋顶显轻。',
      },
      qiangji: {
        name: '戗脊',
        note: '屋面转角处的斜脊，脊上可列小兽，是屋顶的「骨架线」。',
      },
      wadang: {
        name: '瓦当',
        note: '筒瓦最前端的圆瓦头，当面模印纹样，既护檐口又做装饰。',
      },
      dishui: {
        name: '滴水',
        note: '板瓦前端下垂的尖角瓦件，专管把雨水导成一条线滴落，护住墙面。',
      },
    },
  },
};

const LEVELS = [
  { id: 1, name: '入门 · 窗棂', category: 'window', questions: 6, lives: 3, seconds: null },
  { id: 2, name: '门饰 · 门墩', category: 'doorstone', questions: 6, lives: 3, seconds: null },
  { id: 3, name: '檐下 · 砖雕', category: 'brick', questions: 6, lives: 3, seconds: null },
  { id: 4, name: '院门 · 大门形制', category: 'gate', questions: 6, lives: 3, seconds: null },
  { id: 5, name: '综合试炼', category: 'mixed', questions: 8, lives: 3, seconds: 75 },
];

const RULES = {
  comboCap: 5,
  basePoints: 10,
  comboStep: 2,
};

const RANKS = [
  { min: 0.85, title: '大师', desc: '看得懂瓦当，也读得懂礼制。' },
  { min: 0.60, title: '匠人', desc: '构件认得全，眼力已经到家了。' },
  { min: 0.0, title: '学徒', desc: '刚进门，先去院里转两圈。' },
];

if (typeof module === 'object' && module.exports) {
  module.exports = { CATEGORIES, LEVELS, RULES, RANKS };
} else {
  window.SYY = window.SYY || {};
  Object.assign(window.SYY, { CATEGORIES, LEVELS, RULES, RANKS });
}
