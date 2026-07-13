import { registerMock } from './index'

export function setupHRMock() {
  registerMock('get', '/hr/messages', () => {
    return [
      {
        id: 1,
        company: '字节跳动',
        hr_name: '张女士',
        content: '您好，我们在BOSS直聘上看到了您的简历，觉得您非常适合我们团队的高级前端开发工程师岗位，方便约个时间聊聊吗？',
        reply_suggestion: '您好张女士，感谢您的邀请！我对字节跳动的高级前端开发工程师岗位非常感兴趣。请问您方便在以下时间安排一个初步沟通吗？\n1. 本周三下午2:00-4:00\n2. 本周四上午10:00-12:00\n期待与您进一步交流！',
        status: 'pending',
        created_at: '2026-07-13T09:00:00.000Z',
      },
      {
        id: 2,
        company: '美团',
        hr_name: '李先生',
        content: '你好，我是美团到店事业群的技术招聘负责人。看了你的简历，你的技术栈与我们团队非常匹配，想邀请你参加我们的技术面，你看什么时间方便？',
        reply_suggestion: '李先生您好，感谢您的认可！美团的到店业务我一直很关注，非常期待能加入贵团队。本周五全天我都有空，您看是否方便安排？另外想请教一下，技术面一般包含几个环节，需要做什么准备吗？',
        status: 'pending',
        created_at: '2026-07-12T14:30:00.000Z',
      },
      {
        id: 3,
        company: '阿里巴巴',
        hr_name: '王女士',
        content: '同学你好，我们是阿里巴巴CBU技术部，正在招聘前端架构师岗位。请问你目前是在职还是已经离职了？如果方便的话，我们可以先做一个简单的电话沟通。',
        reply_suggestion: '王女士您好，感谢您的联系！阿里CBU技术部的前端架构师岗位我非常感兴趣。我目前仍在职，但正在积极看新的机会。您说的电话沟通非常合适，我的手机号是138****8888，您方便时随时可以联系我。',
        status: 'replied',
        created_at: '2026-07-11T11:00:00.000Z',
      },
      {
        id: 4,
        company: '腾讯',
        hr_name: '陈先生',
        content: '你好，你的简历已通过腾讯云部门的初筛，我们想邀请你参加下周的技术面试。先做一份在线编程题（约1小时），通过后安排视频面试。',
        reply_suggestion: '陈先生您好，感谢通过初筛！我非常愿意参加腾讯云部门的面试。在线编程题我这边没问题，请问题目链接发到我邮箱就可以，收到后我会尽快完成。另外想确认一下，视频面试主要考察哪些方面的技术能力？',
        status: 'pending',
        created_at: '2026-07-10T16:00:00.000Z',
      },
      {
        id: 5,
        company: '京东',
        hr_name: '刘女士',
        content: '您好，我是京东招聘团队的。您的简历已推送到交易前端团队，团队负责人对您的背景很感兴趣。我们计划安排一轮技术电话面试，大概30-45分钟，您方便吗？',
        reply_suggestion: '刘女士您好，感谢京东团队的认可！技术电话面试没问题，下周一至周三的上午10:00-12:00我都方便。期待与负责人交流！',
        status: 'archived',
        created_at: '2026-07-09T10:00:00.000Z',
      },
    ]
  })

  // Get reply suggestions
  registerMock('get', '/hr/messages/:id/suggestions', (params: any) => {
    const id = parseInt(params.id)
    const suggestions: Record<number, string[]> = {
      1: [
        '您好，感谢您的邀请！我对这个岗位非常感兴趣。请问方便在周三下午或周四上午安排一个初步沟通吗？',
        '感谢联系！我很感兴趣。是否能先了解一下团队的 technical stack 和主要业务方向？',
        '您好，感谢关注！我的作品集链接是[...]，您可以先看一下。期待进一步沟通！',
      ],
      2: [
        '感谢您的认可！非常期待加入美团。这周五我全天都有空，您看什么时间方便？',
        '您好，谢谢联系！能否先介绍一下团队的技术栈和主要业务方向？这样我可以更好地准备面试。',
        '感谢邀请！请问面试流程是怎样的，大概需要多长时间能完成所有环节？',
      ],
    }
    return {
      suggestions: suggestions[id] || ['感谢您的联系，我对该岗位很感兴趣，请问什么时间方便进一步沟通？'],
    }
  })

  // Reply
  registerMock('post', '/hr/reply', (params: any) => {
    return null
  })

  // Archive
  registerMock('post', '/hr/messages/:id/archive', () => {
    return null
  })
}